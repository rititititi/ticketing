"""Untrusted screenshots are OCR evidence, never commands. Review is required before publishing."""
import argparse,csv,hashlib,io,json,os,re,subprocess,sys,shutil
from pathlib import Path
from datetime import datetime,timezone,date
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ticket_fields import extract_text_fields,normalize_row,VALID_SECTIONS
from catalog_updates import apply_patch,write_reports
JOB_RE=re.compile(r'^[a-f0-9]{32}$')
ALIASES={'section':['区域','區域','区','區','section'],'row':['排数','排号','排號','排','row'],'seat_as_printed':['座位号','座位號','座号','座號','座位','位置','seat'],'price':['价格','價格','售价','售價','结算价格','price'],'performance_date':['演出日期','日期','时间','date'],'printed_id':['序号','编号','票面编号','id']}

def read_request(root,job):
    if not JOB_RE.fullmatch(job):raise ValueError('Invalid job ID')
    folder=root/'data/upload-jobs'/job
    request=json.loads((folder/'request.json').read_text())
    expected=f'data/upload-jobs/{job}/input.{request["extension"]}'
    if request['extension'] not in ['png','jpg'] or request['input_path']!=expected:raise ValueError('Invalid input image path')
    image=root/expected
    if hashlib.sha256(image.read_bytes()).hexdigest()!=request['sha256']:raise ValueError('Image checksum mismatch')
    return folder,request,image

def ocr_candidates(image,tessdata=None):
    from PIL import Image,ImageOps
    import numpy as np
    im=Image.open(image);im.verify();im=Image.open(image).convert('RGB')
    if im.width*im.height>30000000:raise ValueError('Use a screenshot below 30 megapixels')
    a=np.asarray(im);gray=a.max(axis=2)
    if (gray<90).mean()>.5:gray=255-a.max(axis=2)
    gray=np.where(gray>160,255,0).astype('uint8')
    k=max(20,im.width//4);cs=np.pad(np.cumsum(gray<180,axis=1,dtype=np.int32),((0,0),(1,0)))
    gray[((cs[:,k:]-cs[:,:-k])==k).any(axis=1),:]=255
    gray[:,(gray<180).mean(axis=0)>.55]=255
    scale=max(1,1600/im.width);prepared=Image.fromarray(gray).resize((round(im.width*scale),round(im.height*scale)));prepared=ImageOps.expand(prepared,border=20,fill=255)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'ocr.png';prepared.save(path)
        command=['tesseract',str(path),'stdout','-l','chi_sim+eng','--psm','6','-c','tessedit_create_tsv=1']
        if tessdata:command.extend(['--tessdata-dir',str(tessdata)])
        result=subprocess.run(command,check=True,capture_output=True,text=True,timeout=180,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
    groups={}
    for word in csv.DictReader(io.StringIO(result.stdout),delimiter='\t',quoting=csv.QUOTE_NONE):
        if not word.get('text','').strip() or float(word['conf'])<0:continue
        key=tuple(word[k] for k in ['block_num','par_num','line_num'])
        groups.setdefault(key,[]).append({'text':word['text'],'x':(float(word['left'])+float(word['width'])/2-20)/scale,'y':(float(word['top'])+float(word['height'])/2-20)/scale})
    lines=sorted(groups.values(),key=lambda words:min(w['y'] for w in words))
    # Identify labelled table columns, joining adjacent Chinese OCR tokens before matching.
    header=None;columns={};score=0;header_chunks=[]
    for words in lines:
        words=sorted(words,key=lambda w:w['x']);chunks=[]
        for word in words:
            if chunks and word['x']-chunks[-1][-1]['x']<max(20,im.width*.025):chunks[-1].append(word)
            else:chunks.append([word])
        detected={}
        for chunk in chunks:
            text=''.join(w['text'] for w in chunk).strip('▼vV| ')
            for field,aliases in ALIASES.items():
                if text in aliases:detected[field]=sum(w['x'] for w in chunk)/len(chunk)
        if len(detected)>score:score=len(detected);header=words;columns=detected;header_chunks=chunks
    bounds={}
    if 'row' not in columns and 'section' in columns and 'seat_as_printed' in columns:
        between=[sum(w['x'] for w in chunk)/len(chunk) for chunk in header_chunks if columns['section']<sum(w['x'] for w in chunk)/len(chunk)<columns['seat_as_printed']]
        if len(between)==1:columns['row']=between[0]
    if score>=2:
        centers=sorted(columns.items(),key=lambda p:p[1])
        for n,(field,x) in enumerate(centers):bounds[field]=((centers[n-1][1]+x)/2 if n else 0,(centers[n+1][1]+x)/2 if n+1<len(centers) else im.width)
    rows=[];header_y=min(w['y'] for w in header) if score>=2 else -1
    # Re-read labelled columns independently: avoid Chinese glyphs making F4 look like FA,
    # and avoid the serial/date columns leaking into section and row values.
    column_words={}
    for field in ['section','row','seat_as_printed']:
        if field not in bounds:continue
        left,right=bounds[field];top=max(0,int(header_y+10));crop=im.crop((int(left),top,int(right),im.height))
        channels=crop.split();from PIL import ImageChops
        bright=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).point(lambda p:255 if p>150 else 0)
        factor=max(2,500/max(1,crop.width));bright=bright.resize((round(crop.width*factor),round(crop.height*factor)))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'column.png';bright.save(path)
            whitelist='FT0123456789' if field=='section' else '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/~-()'
            command=['tesseract',str(path),'stdout','-l','eng','--psm','6','-c','tessedit_create_tsv=1','-c','tessedit_char_whitelist='+whitelist]
            if tessdata:command.extend(['--tessdata-dir',str(tessdata)])
            result=subprocess.run(command,check=True,capture_output=True,text=True,timeout=90,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
        column_words[field]=[{'text':w['text'],'y':top+(float(w['top'])+float(w['height'])/2)/factor} for w in csv.DictReader(io.StringIO(result.stdout),delimiter='\t',quoting=csv.QUOTE_NONE) if w.get('text','').strip() and float(w['conf'])>=0]
    for words in lines:
        if min(w['y'] for w in words)<=header_y:continue
        words=sorted(words,key=lambda w:w['x']);raw=' | '.join(w['text'] for w in words)
        fields=extract_text_fields(raw)
        cells={key:' '.join(w['text'] for w in words if left<=w['x']<right) for key,(left,right) in bounds.items()}
        if cells.get('section'):fields['section']=extract_text_fields(cells['section'])['section']
        if cells.get('row'):fields['row']=normalize_row(cells['row'])
        if cells.get('seat_as_printed'):
            combined=extract_text_fields(cells['seat_as_printed'])
            if combined['section']!='UNRESOLVED':fields.update({k:combined[k] for k in ['section','row','seat_as_printed']})
            else:fields['seat_as_printed']=cells['seat_as_printed']
        center=sum(w['y'] for w in words)/len(words)
        for field,candidates in column_words.items():
            nearby=sorted([w for w in candidates if abs(w['y']-center)<max(8,im.width*.008)],key=lambda w:abs(w['y']-center))
            if not nearby:continue
            text=nearby[0]['text']
            if field=='section' and text in VALID_SECTIONS:fields['section']=text
            elif field=='row' and normalize_row(text):fields['row']=normalize_row(text)
            elif field=='seat_as_printed' and re.fullmatch(r'[0-9]?X',text,re.I):fields['seat_as_printed']=text.upper()
        price_text=cells.get('price') or ' '.join(w['text'] for w in words if w['x']>im.width*.78)
        quotes=re.findall(r'(?<!\d)(\d{1,2}[,，]\d{3}|\d{3,5})(?!\d)',price_text)
        price=float(quotes[-1].replace(',','').replace('，','')) if len(quotes)==1 else None
        sold=bool(re.search(r'\bsold\b|已售|售出|售罄',price_text,re.I))
        if not (sold or price is not None or fields['section']!='UNRESOLVED' or re.search(r'\d{6,8}',raw)):continue
        match=re.search(r'(20\d{2})[-/.]?(\d{1,2})[-/.]?(\d{1,2})(?!\d)',fields['date_as_printed'])
        performance=''
        if match:
            try:performance=date(*map(int,match.groups())).isoformat()
            except ValueError:pass
        rows.append({key:fields[key] for key in ['section','row','seat_as_printed']}|dict(price=None if sold else price,sold=sold,performance_date=performance,notes='',raw_ocr=raw))
    if not rows:raise ValueError('No readable option rows. Upload a clearer crop with column headers visible.')
    if len(rows)>1000:raise ValueError('Split very long sheets into images with fewer than 1000 options.')
    return rows,im.width,im.height

def validate_rows(rows):
    if not isinstance(rows,list) or not 1<=len(rows)<=1000:raise ValueError('Review 1–1000 rows')
    result=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid option row')
        clean={}
        for key,limit in [('section',20),('row',80),('seat_as_printed',80),('notes',500),('raw_ocr',3000),('performance_date',10)]:
            value=row.get(key,'')
            if not isinstance(value,str) or len(value)>limit:raise ValueError(f'Invalid {key}')
            clean[key]=value.strip()
        clean['section']=clean['section'].upper() or 'UNRESOLVED'
        if clean['section']!='UNRESOLVED' and clean['section'] not in VALID_SECTIONS:raise ValueError('Unknown section; use UNRESOLVED if uncertain')
        clean['row']=normalize_row(clean['row'])
        if row.get('row') and not clean['row']:raise ValueError('Use a numeric row, range such as 12/13, or a letter row')
        if clean['performance_date']:date.fromisoformat(clean['performance_date'])
        if not isinstance(row.get('sold'),bool):raise ValueError('Set sold explicitly')
        price=row.get('price')
        import math
        if price is not None and (isinstance(price,bool) or not isinstance(price,(int,float)) or not math.isfinite(price) or not 0<=price<=1000000):raise ValueError('Invalid price')
        clean.update(price=None if row['sold'] else price,sold=row['sold']);result.append(clean)
    return result

def publish(root,job):
    folder,request,image=read_request(root,job);review=json.loads((folder/'review.json').read_text())
    if review.get('status')=='published':return
    if review.get('status')!='approved' or review.get('reviewed_all_rows') is not True:raise ValueError('Admin review and approval required')
    rows=validate_rows(review['rows']);catalog=json.loads((root/'data/catalog.json').read_text());index=max(s['source_index'] for s in catalog['sources'])+1
    filename=f'upload-{job}.{request["extension"]}'
    source=dict(source_index=index,source_file=filename,width=review['width'],height=review['height'],sha256=request['sha256'],visual_family=f'UPLOAD-{job[:8]}',family_description='Admin-uploaded screenshot',seller='Unknown',image_link='source-images/'+filename,ocr_line_count=len(rows),coverage_status='All option rows checked and approved by admin',review_status='Admin-reviewed; availability still requires supplier confirmation',previous_source_index=request['base_source_index'],published_at=review.get('approved_at') or request.get('created_at') or '')
    tickets=[]
    for ordinal,row in enumerate(rows,1):
        tickets.append(dict(**{k:row[k] for k in ['section','row','seat_as_printed','sold','price','raw_ocr']},id=f'upload-{job}-{ordinal}',event_id=catalog.get('event_id','nct-wish-gocheok'),source_index=index,source_file=filename,source_row=f'physical-{ordinal}',physical_row=ordinal,source_bbox=None,performance_date=row['performance_date'] or None,date_key=row['performance_date'] or 'unresolved',date_as_printed=extract_text_fields(row['raw_ocr'])['date_as_printed'] or row['performance_date'] or 'Unresolved',seller='Unknown',concert=catalog['concert'],quantity=1,quantity_basis='One per option row is provisional; confirm grouped offers',currency='CNY',supplier_quote_cny=row['price'],customer_price_cny=None,price_as_printed=str(row['price']) if row['price'] is not None else '',availability='sold_out_in_source' if row['sold'] else 'listed_in_source_confirm_with_seller',status='Sold in source' if row['sold'] else 'Admin reviewed · supplier confirmation needed',seating_notes=row['notes'],delivery='See original screenshot',verification='Reviewed and approved by admin against source screenshot',review_flags='Admin-reviewed transcription; seller identity and current stock require confirmation',extraction_status='admin_reviewed',legacy_ocr='',ocr_line_numbers=[],source_color_markings=[]))
    patch=dict(job_id=job,base_source_index=request['base_source_index'],base_source_sha256=request.get('base_source_sha256'),source=source,tickets=tickets)
    updated=apply_patch(catalog,patch)
    (root/'static/sources').mkdir(parents=True,exist_ok=True);shutil.copy2(image,root/'static/sources'/filename)
    (root/'data/updates').mkdir(parents=True,exist_ok=True);(root/'data/updates'/f'{job}.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2))
    (root/'data/catalog.json').write_text(json.dumps(updated,ensure_ascii=False,separators=(',',':')))
    (root/'data/draft2/coverage.json').write_text(json.dumps(updated['coverage'],ensure_ascii=False,indent=2))
    write_reports(updated,root)
    from updates_feed import write_derived
    write_derived(updated,root)
    review.update(status='published',published_source_index=index);(folder/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);parser.add_argument('--phase',choices=['extract','publish'],required=True);parser.add_argument('--tessdata-dir',type=Path);args=parser.parse_args()
    folder,request,image=read_request(ROOT,args.job)
    if args.phase=='publish':
        try:publish(ROOT,args.job)
        except ValueError as error:
            review=json.loads((folder/'review.json').read_text());review.update(status='review',error=str(error));(folder/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
        return
    existing=folder/'review.json'
    if existing.exists() and json.loads(existing.read_text()).get('status') in ['approved','published']:return
    try:
        rows,width,height=ocr_candidates(image,args.tessdata_dir);result=dict(status='review',rows=rows,width=width,height=height)
    except Exception:
        result=dict(status='failed',error='OCR could not read this screenshot. Try a clearer image with visible column headings.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2)
    if len(serialized.encode('utf-8'))>850000:serialized=json.dumps(dict(status='failed',error='Split this very large sheet into smaller screenshots before uploading.'))
    existing.write_text(serialized)
if __name__=='__main__':main()
