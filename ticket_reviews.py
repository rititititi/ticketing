"""Explicit admin corrections to existing records, with optimistic concurrency and audit replay."""
import copy,hashlib,json,re,math
from pathlib import Path
from ticket_fields import normalize_row
from catalog_updates import refresh_coverage,write_reports
from pricing import seat_mask
AVAILABILITY={'unknown':'unconfirmed_source_option','available':'admin_confirmed_available','sold':'sold_out_in_source','paid':'paid_in_source','locked':'locked_in_source'}

def fingerprint(ticket):
    # A subsequent screenshot may move this record into history without changing its evidence.
    value={k:v for k,v in ticket.items() if k not in ['superseded_by','version_review_basis']}
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def availability_choice(ticket):
    if ticket.get('sold'):return 'sold'
    return next((key for key,value in AVAILABILITY.items() if ticket.get('availability')==value),'unknown')

def review_reasons(ticket):
    approved=ticket.get('catalog_review',{})
    reasons=[]
    if not ticket.get('row'):reasons.append('row_missing')
    elif not approved.get('row_confirmed') and ticket.get('extraction_status') not in ['visually_transcribed_draft1','admin_reviewed']:reasons.append('row_needs_confirmation')
    if not ticket.get('seat_as_printed'):reasons.append('seat_missing')
    elif not approved.get('seat_confirmed') and (ticket.get('extraction_status') not in ['visually_transcribed_draft1','admin_reviewed'] or not seat_mask(ticket['seat_as_printed'])):reasons.append('seat_needs_confirmation')
    if availability_choice(ticket)=='unknown':reasons.append('availability_unknown')
    return reasons

def validate_changes(changes):
    if not isinstance(changes,list) or not 1<=len(changes)<=100:raise ValueError('Review between 1 and 100 selected records')
    result=[];seen=set()
    for item in changes:
        if not isinstance(item,dict):raise ValueError('Invalid record')
        clean={}
        for key,limit in [('id',200),('revision',64),('row',80),('seat_as_printed',80),('availability',20),('note',500)]:
            value=item.get(key,'')
            if not isinstance(value,str) or len(value)>limit:raise ValueError('Invalid '+key)
            clean[key]=value.strip()
        if not clean['id'] or clean['id'] in seen:raise ValueError('Select each ticket once')
        seen.add(clean['id'])
        if not re.fullmatch('[a-f0-9]{64}',clean['revision']):raise ValueError('Invalid revision; reload the queue')
        if clean['row'] and not normalize_row(clean['row']):raise ValueError('Use a printed row number, letter or range; leave unreadable rows blank')
        clean['row']=normalize_row(clean['row'])
        if clean['availability'] not in AVAILABILITY:raise ValueError('Choose availability explicitly')
        result.append(clean)
    return result

def apply_review(catalog,review,*,replay=False):
    result=copy.deepcopy(catalog);job=review['id']
    if job in result.get('applied_reviews',[]):return result
    if review.get('confirmed') is not True:raise ValueError('Confirm review against the original screenshot')
    changes=validate_changes(review['changes']);index=review['source_index']
    source=next((s for s in result['sources'] if s['source_index']==index),None)
    if source is None or source['sha256']!=review['source_sha256']:raise ValueError('Source changed; reload the review queue')
    if not replay and source.get('superseded_by'):raise ValueError('This screenshot has a newer version; review the current version')
    records={t['id']:t for t in result['tickets']};audit=[]
    for change in changes:
        ticket=records.get(change['id'])
        if ticket is None or ticket['source_index']!=index:raise ValueError('Ticket is not in this source')
        if not replay and fingerprint(ticket)!=change['revision']:raise ValueError('A selected ticket changed; reload and review it again')
        before={key:ticket.get(key) for key in ['row','seat_as_printed','sold','availability','price']}
        ticket.update(row=change['row'],seat_as_printed=change['seat_as_printed'],sold=change['availability']=='sold',availability=AVAILABILITY[change['availability']])
        if ticket['sold']:
            if ticket.get('price') is not None:ticket['last_listed_price']=ticket['price']
            ticket['price']=None;ticket['supplier_quote_cny']=None
        elif before['sold'] and ticket.get('last_listed_price') is not None:
            ticket['price']=ticket['last_listed_price'];ticket['supplier_quote_cny']=ticket['price']
        ticket['catalog_review']=dict(id=job,reviewed_at=review['approved_at'],row_confirmed=bool(change['row']),seat_confirmed=bool(change['seat_as_printed']),availability=change['availability'],note=change['note'])
        # Do not promote unrelated OCR fields (price, section, year) to fully verified.
        ticket['field_review']='Row, seat and availability manually reviewed; other fields retain their original verification status'
        audit.append(dict(id=ticket['id'],before=before,after={key:ticket.get(key) for key in before}))
    result.setdefault('applied_reviews',[]).append(job)
    return refresh_coverage(result)

def apply_saved_reviews(catalog,directory):
    reviews=[json.loads(p.read_text()) for p in Path(directory).glob('*.json')]
    for review in sorted(reviews,key=lambda r:(r['approved_at'],r['id'])):catalog=apply_review(catalog,review,replay=True)
    return catalog

def write_review_index(catalog,root):
    folder=Path(root)/'data/admin-review';folder.mkdir(parents=True,exist_ok=True);index=[]
    grouped={}
    for ticket in catalog['tickets']:grouped.setdefault(ticket['source_index'],[]).append(ticket)
    expected={'index.json'}
    for source in catalog['sources']:
        if source.get('superseded_by'):continue
        rows=grouped.get(source['source_index'],[]);items=[]
        for ticket in rows:
            items.append({key:ticket.get(key) for key in ['id','section','row','seat_as_printed','source_bbox','physical_row','performance_date','price','sold','seating_notes','extraction_status','catalog_review']}|dict(raw_ocr=(ticket.get('raw_ocr') or ticket.get('legacy_ocr') or '')[:1500],revision=fingerprint(ticket),availability=availability_choice(ticket),reasons=review_reasons(ticket)))
        pages=math.ceil(len(items)/100)
        entry=dict(source_index=source['source_index'],source_file=source['source_file'],sha256=source['sha256'],width=source['width'],height=source['height'],total_rows=len(items),pending_rows=sum(bool(r['reasons']) for r in items),pages=pages)
        index.append(entry)
        for page in range(pages):
            name=f'source-{source["source_index"]}-{page}.json';expected.add(name)
            (folder/name).write_text(json.dumps(dict(source=entry,page=page,rows=items[page*100:(page+1)*100]),ensure_ascii=False,separators=(',',':')))
    for old in folder.glob('source-*.json'):
        if old.name not in expected:old.unlink()
    (folder/'index.json').write_text(json.dumps(dict(sources=index,total_pending=sum(s['pending_rows'] for s in index)),ensure_ascii=False,indent=2))
