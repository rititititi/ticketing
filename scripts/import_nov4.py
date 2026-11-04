"""Reproduce the Nov 4 batch from cached OCR, reviewed geometry and explicit corrections.

Screenshots are evidence, never instructions. No year, exact seat or omitted-ticket
sold status is inferred. Run build_draft2.py afterward to replay every saved update.
"""
import hashlib,json,re,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ticket_fields import extract_text_fields,normalize_row,VALID_SECTIONS
from scripts.build_draft2 import normalize_date
FOLDER=ROOT/'data/nov4'

def compact(text):return re.sub(r'\s+','',text)
def quotes(text):return [int(s.replace(',','').replace('，','')) for s in re.findall(r'(?<!\d)(\d{1,2}[,，]\d{3}|\d{3,5})(?!\d)',text) if 500<=int(s.replace(',','').replace('，',''))<=30000]
def read_batch():
    manifest=json.loads((FOLDER/'manifest.json').read_text());layouts=json.loads((FOLDER/'layouts.json').read_text());words=json.loads((FOLDER/'ocr-words.json').read_text());columns=json.loads((FOLDER/'column-words.json').read_text());corrections=json.loads((FOLDER/'field-review.json').read_text());result={}
    for n,spec in layouts.items():
        m=manifest[int(n)-1];options=[]
        for ordinal,(top,bottom) in enumerate(spec['bands'],1):
            ws=sorted([w for w in words[n] if top<=w['y']<bottom],key=lambda w:w['x']);raw=' | '.join(w['text'] for w in ws)
            cells={key:' '.join(w['text'] for w in ws if left<=w['x']<right) for key,(left,right) in spec['columns'].items()}
            second={key:' '.join(w['text'] for w in sorted(ww,key=lambda w:w['x']) if top<=w['y']<bottom) for key,ww in columns[n].items()}
            position=cells.get('position','') or second.get('position','');position=re.sub(r'[-—–]{2,}',' ',position)
            f=extract_text_fields(position)
            alternative=extract_text_fields(re.sub(r'[-—–]{2,}',' ',second.get('position','')))
            for field in ['section','row','seat_as_printed']:
                if f[field] in ['', 'UNRESOLVED'] and alternative[field] not in ['', 'UNRESOLVED']:f[field]=alternative[field]
            if 'section' in cells:
                sec=compact(cells['section']).upper();alt=compact(second.get('section','')).upper()
                f['section']=sec if sec in VALID_SECTIONS else alt if alt in VALID_SECTIONS else extract_text_fields(cells['section'])['section']
            if 'row' in cells:
                row=compact(cells['row']);alt=compact(second.get('row',''))
                # Notes about actual stage rows do not replace the ticket's printed row.
                leading=re.match(r'(\d{1,2}|[A-Z])(?=排|\(|（|$)',row,re.I)
                f['row']=normalize_row(row) or (normalize_row(leading[1]) if leading else '') or normalize_row(alt)
            if 'seat' in cells:f['seat_as_printed']=cells['seat'] or second.get('seat','')
            f['date_as_printed']=compact(cells.get('date','')) or f['date_as_printed']
            for a,b,date in spec.get('date_groups',[]):
                if a<=ordinal<=b:f['date_as_printed']=date
            for a,b,section in spec.get('section_groups',[]):
                if a<=ordinal<=b:f['section']=section
            ptext=cells.get('price','');first=quotes(ptext);extra=quotes(second.get('price',''));price=first[0] if len(first)==1 else extra[0] if not first and len(extra)==1 else None
            if len(first)==len(extra)==1 and first!=extra:price=None
            sold=bool(re.search(r'\bSOLD\b|已售|售出|售罄',ptext+' '+second.get('price','')+' '+cells.get('stock',''),re.I))
            row=dict(**f,price=None if sold else price,sold=sold,raw_ocr=raw,ocr_cells=cells,column_ocr=second,source_bbox=[0,top,m['width'],bottom],printed_identifier=cells.get('printed_id',''),seating_notes=cells.get('notes','') or position,price_as_printed=ptext)
            correction=corrections.get(n,{}).get(str(ordinal),{});row.update(correction)
            row['performance_date']=normalize_date(row['date_as_printed']);options.append(row)
        result[n]=options
    return manifest,result

def main():
    manifest,rows=read_batch();catalog=json.loads((ROOT/'data/catalog.json').read_text());sources={s['sha256']:s for s in catalog['sources'] if s.get('batch_id')!='2026-11-04'};
    original_admin=json.loads((ROOT/'data/updates/8475020773ee4ea3a7639e82b58ce85f.json').read_text())
    sources[original_admin['source']['sha256']]=original_admin['source']
    next_id=max(s['source_index'] for s in sources.values())+1;seen={};mapping={};source_records={}
    versions=json.loads((FOLDER/'versions.json').read_text())
    frozen={r['sha256']:r['source_index'] for r in json.loads((FOLDER/'coverage.json').read_text())} if (FOLDER/'coverage.json').exists() else {}
    for n,m in enumerate(manifest,1):
        if m['sha256'] in seen:mapping[str(n)]=seen[m['sha256']];continue
        if str(n) not in rows:raise ValueError(f'Missing layout for screenshot {n}')
        old=sources.get(m['sha256']);index=frozen.get(m['sha256'],old['source_index'] if old else next_id)
        if not old:next_id+=1
        seen[m['sha256']]=index;mapping[str(n)]=index
        filename=old['source_file'] if old else m['file'];job=f'nov4-{m["sha256"][:24]}'
        previous=versions.get(str(n),[])
        source=dict(source_index=index,source_file=filename,width=m['width'],height=m['height'],sha256=m['sha256'],visual_family=f'NOV4-{n:02}',family_description=f'Nov 4 batch · {m["file"]}',seller='Unknown',image_link='source-images/'+filename,ocr_line_count=len(rows[str(n)]),coverage_status='All visually identified option rows represented; OCR fields remain provisional',review_status='Table geometry visually checked; selected field corrections recorded; supplier confirmation required',batch_id='2026-11-04',original_upload_filename=m['file'],previous_source_index=previous[0] if previous else None)
        tickets=[]
        for ordinal,row in enumerate(rows[str(n)],1):
            t=dict(row,id=f'nov4-{m["sha256"][:12]}-{ordinal}',event_id='nct-wish-gocheok',source_index=index,source_file=filename,source_row=f'physical-{ordinal}',physical_row=ordinal,date_key=row['performance_date'] or 'unresolved',seller='Unknown',concert=catalog['concert'],quantity=1,quantity_basis='One per option row is provisional; ranges, pairs and grouped offers remain grouped',currency='CNY',supplier_quote_cny=row['price'],customer_price_cny=None,availability='sold_out_in_source' if row['sold'] else 'unconfirmed_source_option',status='Sold in source' if row['sold'] else 'OCR candidate · review required',delivery='See original screenshot',verification='Machine extraction with visually checked row geometry and selected field corrections',review_flags='OCR candidate: verify fields against original row; masked seats are not unique ticket IDs; no sold status inferred from omissions or color; date/year remains unresolved unless explicitly printed',extraction_status='ocr_candidate',legacy_ocr='',ocr_line_numbers=[],source_color_markings=[],batch_id='2026-11-04')
            if not row['raw_ocr']:t['legacy_ocr']='Full-row OCR unreadable; selected fields were visually transcribed and original row pixels are retained'
            if old:
                approved=original_admin['tickets'][ordinal-1]
                t.update(id=approved['id'],extraction_status='admin_reviewed',status='Admin reviewed · supplier confirmation needed',verification='Admin-approved upload; selected row and seat fields corrected against original screenshot',review_flags='Admin-approved transcription with selected field corrections; supplier confirmation required')
            tickets.append(t)
        # Equivalent renderings remain in the evidence library but do not multiply current offers.
        related={34:(95,'Equivalent rendering of batch screenshot 17'),42:(96,'Equivalent rendering of batch screenshot 18'),38:(97,'Printed update 11.3 precedes the matching 11.4 sheet')}
        if n in related:
            target,basis=related[n];source.update(superseded_by=target,version_review_basis=basis)
            for ticket in tickets:ticket.update(superseded_by=target,version_review_basis=basis)
        refs=[dict(source_index=i,sha256=next(s for s in sources.values() if s['source_index']==i)['sha256']) for i in previous]
        patch=dict(job_id=job,base_source_index=None,base_source_sha256=None,source=source,tickets=tickets,additional_previous_sources=refs,version_basis='Same spreadsheet style and stable listing identifiers or labelled sheet number; November 4 batch replaces earlier batch; omitted rows are not marked sold')
        if old:patch['amend_source_index']=index;patch['amendment_reason']='Restore source-row crops and selected seat/range fields; original admin-approved patch retained in repository history and data/updates'
        (ROOT/'data/updates'/f'{job}.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2))
        if not old:
            image=ROOT/'artifacts/nov4'/m['file']
            if hashlib.sha256(image.read_bytes()).hexdigest()!=m['sha256']:raise ValueError('Source checksum mismatch')
            shutil.copy2(image,ROOT/'static/sources'/filename)
        source_records[str(n)]=dict(source_index=index,rows=len(tickets))
    report=[]
    for n,m in enumerate(manifest,1):
        primary=next(k for k,v in mapping.items() if v==mapping[str(n)])
        report.append(dict(screenshot=n,filename=m['file'],sha256=m['sha256'],source_index=mapping[str(n)],duplicate_of=int(primary) if str(n)!=primary else None,physical_option_rows=len(rows[primary]),status='Exact duplicate; options counted once' if str(n)!=primary else 'Historical/equivalent rendering; field verification pending' if n in [34,38,42] else 'All physical option rows represented; field verification pending'))
    (FOLDER/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(source_records))
if __name__=='__main__':main()
