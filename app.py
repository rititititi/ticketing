import csv
import io
import os
import secrets
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from openpyxl import load_workbook

app = Flask(__name__)
from explorer import explorer
app.register_blueprint(explorer)
Path(app.instance_path).mkdir(exist_ok=True)
key = Path(app.instance_path) / 'session-key'
if not key.exists():
    key.write_text(secrets.token_hex(32))
app.secret_key = key.read_text()
app.config.update(MAX_CONTENT_LENGTH=5 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
DB = os.environ.get('DATABASE_PATH', str(Path(app.instance_path) / 'tickets.sqlite'))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

with db() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS concerts(id INTEGER PRIMARY KEY, name TEXT NOT NULL, venue TEXT NOT NULL, published INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY, concert_id INTEGER, supplier_id TEXT, date TEXT, section TEXT, row_number TEXT, seat TEXT, notes TEXT, delivery TEXT, cost INTEGER, price INTEGER, quantity INTEGER, available INTEGER DEFAULT 1, UNIQUE(concert_id,supplier_id));
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, reference TEXT UNIQUE, ticket_id INTEGER, name TEXT, email TEXT, status TEXT DEFAULT 'pending', created TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    if not c.execute('SELECT 1 FROM concerts').fetchone():
        c.execute('INSERT INTO concerts(name,venue) VALUES (?,?)', ('NCT WISH · Sample concert', 'Gocheok Sky Dome · Seoul'))

@app.before_request
def csrf():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(24)
    if request.method == 'POST' and not secrets.compare_digest(request.form.get('csrf', ''), session['csrf']):
        abort(400, 'Please refresh the page and try again.')

def admin(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped

@app.route('/')
def home():
    return render_template('explorer.html')

@app.route('/concert/<int:cid>')
def concert(cid):
    with db() as c:
        show = c.execute('SELECT * FROM concerts WHERE id=? AND published=1', (cid,)).fetchone()
        if not show:
            abort(404)
        tickets = c.execute('SELECT * FROM tickets WHERE concert_id=? AND available=1 ORDER BY date,price', (cid,)).fetchall()
    return render_template('concert.html', show=show, tickets=tickets)

@app.post('/book/<int:tid>')
def book(tid):
    name, email = request.form.get('name','').strip(), request.form.get('email','').strip()
    if not name or len(name)>100 or '@' not in email or len(email)>254:
        abort(400, 'Enter a name and valid email address.')
    ref = secrets.token_hex(6).upper()
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        ticket = c.execute('SELECT t.* FROM tickets t JOIN concerts s ON s.id=t.concert_id WHERE t.id=? AND t.available=1 AND s.published=1', (tid,)).fetchone()
        if not ticket:
            abort(409, 'This listing is no longer available.')
        held = c.execute("SELECT count(*) FROM orders WHERE ticket_id=? AND status IN ('pending','confirmed','paid','delivered')", (tid,)).fetchone()[0]
        if held >= ticket['quantity']:
            abort(409, 'All tickets in this listing have active requests. Please choose another option.')
        c.execute('INSERT INTO orders(reference,ticket_id,name,email) VALUES (?,?,?,?)', (ref,tid,name,email))
    return render_template('success.html', reference=ref)

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        password = os.environ.get('ADMIN_PASSWORD','')
        if password and secrets.compare_digest(request.form.get('password',''), password):
            session['admin'] = True
            return redirect(url_for('dashboard'))
        flash('Login unavailable or incorrect password.')
    return render_template('login.html')

@app.post('/admin/logout')
@admin
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin')
@admin
def dashboard():
    with db() as c:
        concerts = c.execute('SELECT * FROM concerts').fetchall()
        tickets = c.execute('SELECT t.*,s.name AS concert FROM tickets t JOIN concerts s ON s.id=t.concert_id').fetchall()
        orders = c.execute('SELECT o.*,t.section,t.seat,s.name AS concert FROM orders o JOIN tickets t ON t.id=o.ticket_id JOIN concerts s ON s.id=t.concert_id ORDER BY o.id DESC').fetchall()
    return render_template('admin.html', concerts=concerts,tickets=tickets,orders=orders)

@app.post('/admin/concert')
@admin
def add_concert():
    name,venue = request.form.get('name','').strip(),request.form.get('venue','').strip()
    if not name or not venue:
        abort(400)
    with db() as c:
        c.execute('INSERT INTO concerts(name,venue) VALUES (?,?)',(name,venue))
    return redirect(url_for('dashboard'))

@app.post('/admin/publish/<int:cid>')
@admin
def publish(cid):
    with db() as c:
        c.execute('UPDATE concerts SET published=1-published WHERE id=?',(cid,))
    return redirect(url_for('dashboard'))

FIELDS = {'supplier_id':'Supplier listing ID', 'date':'Performance date', 'section':'Tier / section', 'row_number':'Row', 'seat':'Seat', 'notes':'Seating notes / quantity notes', 'delivery':'Delivery method', 'cost':'Supplier cost (CNY)', 'price':'Selling price (CNY)', 'quantity':'Explicit ticket quantity'}
ALIASES = {'supplier_id':['序号','id','supplier id'], 'date':['演出日期','演出日','date'], 'section':['区域','区','section'], 'row_number':['排','排数','row'], 'seat':['座位','座号','seat number','seat'], 'notes':['座位备注','备注','notes'], 'delivery':['交付备注','delivery'], 'cost':['价格','原价','og price','original price','cost'], 'price':['售价','selling price'], 'quantity':['数量','quantity']}

@app.post('/admin/import')
@admin
def upload():
    file = request.files.get('file')
    if not file:
        abort(400)
    try:
        if file.filename.lower().endswith('.xlsx'):
            wb = load_workbook(file,read_only=True,data_only=True)
            rows = list(wb.active.iter_rows(values_only=True))
            wb.close()
        elif file.filename.lower().endswith('.csv'):
            rows = list(csv.reader(io.StringIO(file.read().decode('utf-8-sig'))))
        else:
            raise ValueError('Use an .xlsx or UTF-8 .csv file.')
        rows = [[str(v).strip() if v is not None else '' for v in r] for r in rows]
        # Supplier sheets often have a merged title above the column headings.
        header_index = next((i for i,r in enumerate(rows[:20]) if sum(bool(v) for v in r)>=4), None)
        if header_index is None or len(rows)>5001:
            raise ValueError('Expected a heading row and at most 5,000 data rows.')
        headers = rows[header_index]
        data = [r for r in rows[header_index+1:] if sum(bool(v) for v in r)>=2]
        token = secrets.token_hex(16)
        Path(app.instance_path, token+'.json').write_text(__import__('json').dumps({'headers':headers,'rows':data,'cid':int(request.form['concert_id'])}))
        session['import_token'] = token
        mapping = {f:next((i for i,h in enumerate(headers) if h.lower() in ALIASES[f]),-1) for f in FIELDS}
        return render_template('import.html',headers=headers,rows=data[:10],fields=FIELDS,mapping=mapping,count=len(data))
    except (ValueError,KeyError, OSError, __import__('zipfile').BadZipFile) as e:
        flash('Import failed: '+str(e))
        return redirect(url_for('dashboard'))

@app.post('/admin/import/commit')
@admin
def commit_import():
    token = session.get('import_token')
    if not token:
        abort(400)
    path = Path(app.instance_path,token+'.json')
    payload = __import__('json').loads(path.read_text())
    prepared = []
    try:
        for number,row in enumerate(payload['rows'],start=1):
            def value(field):
                index = int(request.form.get(field,-1))
                return row[index].strip() if 0<=index<len(row) else ''
            sid = value('supplier_id')
            if not sid:
                raise ValueError(f'Row {number}: supplier ID is required for safe updates.')
            date = value('date').split(' ')[0].replace('-','').replace('/','')
            date = datetime.strptime(date,'%Y%m%d').strftime('%Y-%m-%d')
            def money(field):
                amount = Decimal(value(field))
                if not amount.is_finite() or amount<=0 or amount.as_tuple().exponent < -2:
                    raise ValueError('Prices must be positive CNY amounts with at most two decimal places.')
                return int(amount*100)
            cost,price = money('cost'),money('price')
            qty = int(value('quantity') or '1')
            if qty<1 or qty>100:
                raise ValueError('Quantity must be between 1 and 100.')
            prepared.append((payload['cid'],sid,date,value('section'),value('row_number'),value('seat'),value('notes'),value('delivery'),cost,price,qty))
        if len({r[1] for r in prepared}) != len(prepared):
            raise ValueError('Duplicate supplier IDs: give each listing a stable unique ID.')
        with db() as c:
            for row in prepared:
                c.execute('''INSERT INTO tickets(concert_id,supplier_id,date,section,row_number,seat,notes,delivery,cost,price,quantity) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(concert_id,supplier_id) DO UPDATE SET date=excluded.date,section=excluded.section,row_number=excluded.row_number,seat=excluded.seat,notes=excluded.notes,delivery=excluded.delivery,cost=excluded.cost,price=excluded.price,quantity=excluded.quantity''',row)
        path.unlink()
        session.pop('import_token',None)
        flash(f'Imported {len(prepared)} listings. Review them before publishing. Missing rows were not automatically marked sold out.')
    except (ValueError,InvalidOperation) as e:
        flash('No changes saved: '+str(e))
    return redirect(url_for('dashboard'))

@app.post('/admin/ticket/<int:tid>')
@admin
def availability(tid):
    with db() as c:
        c.execute('UPDATE tickets SET available=1-available WHERE id=?',(tid,))
    return redirect(url_for('dashboard'))

@app.post('/admin/order/<int:oid>')
@admin
def order_status(oid):
    transitions = {'pending':['confirmed','cancelled'],'confirmed':['paid','cancelled'],'paid':['delivered'],'delivered':[],'cancelled':[]}
    with db() as c:
        order = c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
        status = request.form.get('status')
        if not order or status not in transitions[order['status']]:
            abort(400,'Invalid order transition.')
        c.execute('UPDATE orders SET status=? WHERE id=?',(status,oid))
    return redirect(url_for('dashboard'))

@app.template_filter('cny')
def cny(amount):
    return f'¥{amount/100:,.2f}'

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000)
