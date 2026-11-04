"""Compile all screenshot table rows, keeping OCR candidates separate from visual transcription.

Inputs are immutable draft-1 demo, reviewed row geometry and cached OCR evidence.
No seller identity, year, exact seat, stock, or color legend is inferred.
"""
import argparse,csv,hashlib,io,json,re,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from ticket_fields import extract_text_fields, normalize_row

def baseline():
    with zipfile.ZipFile(ROOT/'concert-atlas-demo.zip') as z:
        html=z.read('concert-atlas/index.html').decode()
    return json.loads(re.search(r'<script id="catalog-data" type="application/json">(.*?)</script>',html,re.S)[1])

def normalize_date(text):
    compact=re.sub(r'\s+','',text)
    m=re.search(r'(202[67])[-/.]?(0?1)[-/.]?(1[56])(?!\d)',compact)
    if m:return f'{m[1]}-01-{m[3]}'
    # No assumed year for 1.15, Jan 15, or literal November dates.
    return None


def number(text):
    ns=re.findall(r'(?<!\d)(\d{1,2}[,，]\d{3}|\d{4,5})(?!\d)',text)
    return [int(n.replace(',','').replace('，','')) for n in ns if 500<=int(n.replace(',','').replace('，',''))<=30000]

def build():
    base=baseline();overrides=json.loads((ROOT/'data/draft2/field-review.json').read_text());layouts=json.loads((ROOT/'data/draft2/row-layouts.json').read_text())
    row_reviews=json.loads((ROOT/'data/row-corrections.json').read_text())
    allwords=json.loads((ROOT/'data/draft2/ocr-words.json').read_text())
    result=[];coverage=[]
    for source in base['sources']:
        i=source['source_index'];layout=layouts[str(i)];words=allwords[str(i)]
        image=ROOT/'static/sources'/source['source_file']
        assert hashlib.sha256(image.read_bytes()).hexdigest()==source['sha256']
        old=[t for t in base['tickets'] if t['source_index']==i]
        if old:assert len(old)==len(layout['bands']),(i,len(old),len(layout['bands']))
        counts=Counter()
        for ordinal,(top,bottom) in enumerate(layout['bands'],1):
            center=(top+bottom)/2
            ws=sorted([w for w in words if top<=w['y']<bottom],key=lambda w:w['x'])
            fresh=' | '.join(w['text'] for w in ws)
            previous=[l for l in base['ocr'] if l['source_index']==i and top<=l['image_y_fraction']*source['height']<bottom]
            legacy='\n'.join(l['ocr_text'] for l in previous)
            raw=fresh or legacy
            fields=extract_text_fields(raw)
            cols={name:' '.join(w['text'] for w in ws if a*source['width']<=w['x']<b*source['width']) for name,(a,b) in layout.get('columns',{}).items()}
            if cols:
                if 'section' in cols:
                    candidate=extract_text_fields(cols['section'])['section']
                    fields['section']=candidate
                if 'row' in cols:fields['row']=normalize_row(cols['row'])
                if 'seat' in cols:fields['seat_as_printed']=cols['seat'].strip()
                if 'position' in cols:
                    pos=extract_text_fields(cols['position'])
                    fields.update({k:pos[k] for k in ('section','row','seat_as_printed')})
                if cols.get('date'):fields['date_as_printed']=cols['date']
            legacy_fields=extract_text_fields(legacy)
            for key in ('section','row','seat_as_printed','date_as_printed'):
                if (not fields[key] or fields[key]=='UNRESOLVED') and legacy_fields[key] and legacy_fields[key]!='UNRESOLVED':fields[key]=legacy_fields[key]
            for first,last,section in layout.get('section_groups',[]):
                if first<=ordinal<=last:fields['section']=section
            for first,last,date in layout.get('date_groups',[]):
                if first<=ordinal<=last:fields['date_as_printed']=date
            for a,b,date in layout.get('date_y_groups',[]):
                if a<=center<b:fields['date_as_printed']=date
            for a,b,section in layout.get('section_y_groups',[]):
                if a<=center<b:fields['section']=section
            price_text=cols.get('price') if 'price' in cols else ' '.join(w['text'] for w in ws if w['x']>.78*source['width'])
            price_candidates=number(price_text or '')
            # Legacy OCR may restore a quote missed by the second pass. Keep disagreements unresolved.
            old_numbers=number(legacy)
            price=price_candidates[-1] if len(price_candidates)==1 else None
            if not price_candidates and old_numbers:price=old_numbers[-1]
            if price is None and not old_numbers and len(number(raw))==1:price=number(raw)[0]
            conflicts=[]
            if price is not None and old_numbers and price!=old_numbers[-1]:
                conflicts.append('OCR passes disagree on quote; numeric quote withheld')
                price=None
            reviewed={**overrides.get(str(i),{}).get(str(ordinal),{}),**row_reviews.get(str(i),{}).get(str(ordinal),{})}
            fields.update({k:v for k,v in reviewed.items() if k in fields})
            if 'price' in reviewed:price=reviewed['price']
            sold=bool(re.search(r'\bsold\b|已售|售出',price_text or '',re.I))
            flags=['OCR candidate: verify fields against the highlighted source row','Seller and version order unknown; availability requires supplier confirmation']+conflicts
            if not fields['date_as_printed']:flags.append('Date unreadable or not captured')
            performance=normalize_date(fields['date_as_printed'])
            if not performance:flags.append('Year/date unresolved; no year inferred')
            elif performance.startswith('2026'):flags.append('2026 printed in source retained; conflicts with 2027 sheets')
            if fields['section']=='UNRESOLVED':flags.append('Section unreadable; retained in review queue')
            if not fields['row']:flags.append('Row unreadable or range; consult original')
            if not fields['seat_as_printed']:flags.append('Seat not captured; no exact seat inferred')
            if price is None and not sold:flags.append('Numeric quote unresolved')
            confidences=[w['confidence'] for w in ws]
            if not confidences or sum(confidences)/len(confidences)<75:flags.append('Low OCR confidence')
            t=dict(source_index=i,source_file=source['source_file'],source_row=f'physical-{ordinal}',id=f'src-{i}-physical-{ordinal}',seller='Unknown',concert=base['concert'],**fields,performance_date=performance,date_key=performance or 'unresolved',quantity=1,quantity_basis='Draft 1 convention: one per source row, not confirmed; grouped offers remain grouped',supplier_quote_cny=price,price=price,price_as_printed=price_text or '',currency='CNY',customer_price_cny=None,face_value_as_printed=cols.get('face'),availability='sold_out_in_source' if sold else 'unconfirmed_source_option',sold=sold,status='Sold in source' if sold else 'OCR candidate · review required',seating_notes=cols.get('notes','') or raw,delivery='Not independently verified; consult source',verification='Machine extracted draft; not visually verified',review_flags='; '.join(flags),extraction_status='ocr_candidate')
            if old:
                t.update(old[ordinal-1]);t['extraction_status']='visually_transcribed_draft1'
            t.update(physical_row=ordinal,source_bbox=[0,top,source['width'],bottom],raw_ocr=fresh,legacy_ocr=legacy,ocr_line_numbers=[l['line_number'] for l in previous],ocr_cells=cols,printed_identifier=cols.get('printed_id',''),mean_ocr_confidence=round(sum(confidences)/len(confidences),1) if confidences else None)
            t['source_color_markings']=layout.get('row_color_markings',[[]]*len(layout['bands']))[ordinal-1]
            if t['source_color_markings']:
                t['review_flags']+='; Source color marking: '+', '.join(t['source_color_markings'])+' (availability meaning not inferred)'
            if i in (15,56,58):
                if 'green' in t['source_color_markings']:t['availability']='paid_in_source';t['review_flags']+='; Green = 已付款 / paid in source legend; not confirmed available'
                elif 'yellow' in t['source_color_markings']:t['availability']='locked_in_source';t['review_flags']+='; Yellow = 已锁定 / locked in source legend; not confirmed available'
            if reviewed.get('sold'):
                t.update(sold=True,availability='sold_out_in_source',status='Sold in source',price=None,supplier_quote_cny=None)
            if reviewed.get('basis'):t['row_review_basis']=reviewed['basis']
            if reviewed:t['field_review']='Selected fields visually checked in draft 2; remaining fields retain extraction status'
            if not raw: t['extraction_status']='unreadable_row';t['review_flags']+='; No OCR text: original row retained for manual transcription'
            result.append(t);counts[t['extraction_status']]+=1
        source_rows=[t for t in result if t['source_index']==i]
        field_gaps={
            'unresolved_section_rows':sum(t['section']=='UNRESOLVED' for t in source_rows),
            'unresolved_row_rows':sum(not t['row'] for t in source_rows),
            'unresolved_seat_rows':sum(not t['seat_as_printed'] for t in source_rows),
            'unresolved_date_rows':sum(not t['performance_date'] for t in source_rows),
            'unresolved_quote_rows':sum(t['price'] is None and not t['sold'] for t in source_rows),
        }
        source.update(field_gaps)
        source.update(physical_option_rows=len(layout['bands']),extracted_rows=len(layout['bands']),ocr_candidate_rows=counts['ocr_candidate'],unreadable_rows=counts['unreadable_row'],coverage_status='All identified table rows represented; field verification pending' if counts['ocr_candidate']+counts['unreadable_row'] else 'All rows visually transcribed in draft 1; supplier confirmation pending',review_status='Field review required; physical row coverage is separate from transcription accuracy')
        coverage.append({k:source[k] for k in ['source_index','source_file','sha256','visual_family','physical_option_rows','extracted_rows','visually_transcribed_rows','ocr_candidate_rows','unreadable_rows','unresolved_section_rows','unresolved_row_rows','unresolved_seat_rows','unresolved_date_rows','unresolved_quote_rows','coverage_status']})
    base.update(tickets=result,draft_version=2,coverage=coverage,extraction_summary=dict(total_source_images=len(coverage),total_option_rows=len(result),visually_transcribed_rows=sum(c['visually_transcribed_rows'] for c in coverage),ocr_candidate_rows=sum(c['ocr_candidate_rows'] for c in coverage),unreadable_rows=sum(c['unreadable_rows'] for c in coverage),note='Physical row coverage does not establish field accuracy. OCR candidates are not verified inventory.'))
    base['event_id']='nct-wish-gocheok'
    for ticket in result:ticket['event_id']=base['event_id']
    from catalog_updates import apply_saved_updates
    base=apply_saved_updates(base,ROOT/'data/updates')
    from ticket_reviews import apply_saved_reviews
    base=apply_saved_reviews(base,ROOT/'data/reviews');coverage=base['coverage'];result=base['tickets']
    (ROOT/'data/catalog.json').write_text(json.dumps(base,ensure_ascii=False,separators=(',',':')))
    (ROOT/'data/draft2/coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
    from catalog_updates import write_reports
    write_reports(base,ROOT)
    from updates_feed import write_derived
    write_derived(base,ROOT)
    print(json.dumps(base['extraction_summary'],indent=2))
if __name__=='__main__':build()
