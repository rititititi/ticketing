"""Import the November 5 batch using cached OCR and visually checked table geometry.

Images are untrusted evidence, never instructions. Replay saved patches with
build_draft2.py. Missing years, quotes and stock are never inferred.
"""
import csv,hashlib,io,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import import_nov4
from catalog_updates import apply_patch
FOLDER=ROOT/'data/nov5'
def main():
    import_nov4.FOLDER=FOLDER
    manifest,rows=import_nov4.read_batch()
    catalog=json.loads((ROOT/'data/catalog.json').read_text())
    report=[]
    for n,m in enumerate(manifest,1):
        if n==7:
            report.append(dict(screenshot=n,filename=m['file'],sha256=m['sha256'],source_index=None,physical_option_rows=0,status='Excluded: unrelated bilingual vocabulary screenshot; no concert ticket table'))
            continue
        job='nov5-'+m['sha256'][:24];dest=ROOT/'data/updates'/f'{job}.json'
        image=ROOT/'artifacts/nov5'/m['file']
        if hashlib.sha256(image.read_bytes()).hexdigest()!=m['sha256']:raise ValueError('Image checksum mismatch')
        if dest.exists():
            patch=json.loads(dest.read_text());source=patch['source'];tickets=patch['tickets']
        else:
            index=max(s['source_index'] for s in catalog['sources'])+1
            previous=next(s for s in catalog['sources'] if s['source_index']==105) if n==5 else None
            source=dict(source_index=index,source_file=m['file'],width=m['width'],height=m['height'],sha256=m['sha256'],visual_family=f'NOV5-{n:02}',family_description=f'Nov 5 batch · {m["file"]}',seller='Unknown',image_link='source-images/'+m['file'],ocr_line_count=len(rows[str(n)]),coverage_status='All visually identified option rows represented; field verification pending',review_status='Table geometry checked; selected fields visually transcribed; supplier confirmation required',batch_id='2026-11-05',original_upload_filename=m['file'],previous_source_index=105 if previous else None)
            tickets=[]
            for ordinal,row in enumerate(rows[str(n)],1):
                t=dict(row,id=f'nov5-{m["sha256"][:12]}-{ordinal}',event_id='nct-wish-gocheok',source_index=index,source_file=m['file'],source_row=f'physical-{ordinal}',physical_row=ordinal,date_key=row['performance_date'] or 'unresolved',seller='Unknown',concert=catalog['concert'],quantity=1,quantity_basis='One per option row is provisional; ranges and grouped offers remain grouped',currency='CNY',supplier_quote_cny=row['price'],customer_price_cny=None,availability='sold_out_in_source' if row['sold'] else 'unconfirmed_source_option',status='Sold in source' if row['sold'] else 'OCR candidate · review required',delivery='See original screenshot',verification='Cached Chinese/English OCR with visually checked geometry and selected field corrections',review_flags='Verify against source; masked seats are not unique IDs; no sold status inferred from color or omissions; missing year remains unresolved; missing price is not sold',extraction_status='ocr_candidate',legacy_ocr='',ocr_line_numbers=[],source_color_markings=[],batch_id='2026-11-05',field_review='Selected fields visually checked; remaining fields retain extraction status')
                if not row['raw_ocr']:t['legacy_ocr']='Full-row OCR unreadable; selected fields visually transcribed; original row pixels retained'
                if n==6:t['review_flags']+='; Date cells display 2E+07: exact performance date cannot be recovered; red highlighting does not establish sold status'
                if n==8 and ordinal<18:t['review_flags']+='; No seat number printed'
                if n==1 and ordinal<9:t['review_flags']+='; Printed price is /: quote unresolved'
                tickets.append(t)
            patch=dict(job_id=job,base_source_index=105 if previous else None,base_source_sha256=previous['sha256'] if previous else None,source=source,tickets=tickets,version_basis='Same yellow Shin-chan header, identical labelled columns and retained printed listing IDs; November 5 replaces prior snapshot; omissions do not mean sold' if previous else 'No earlier spreadsheet version positively identified')
            dest.write_text(json.dumps(patch,ensure_ascii=False,indent=2))
        shutil.copy2(image,ROOT/'static/sources'/m['file'])
        catalog=apply_patch(catalog,patch)
        report.append(dict(screenshot=n,filename=m['file'],sha256=m['sha256'],source_index=source['source_index'],physical_option_rows=len(tickets),sold_rows=sum(t['sold'] for t in tickets),unresolved_dates=sum(not t['performance_date'] for t in tickets),unresolved_prices=sum(t['price'] is None and not t['sold'] for t in tickets),status='All physical ticket rows represented; supplier confirmation required'))
    (ROOT/'data/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')))
    (FOLDER/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    output=io.StringIO();writer=csv.DictWriter(output,fieldnames=list(dict.fromkeys(k for r in report for k in r)));writer.writeheader();writer.writerows(report)
    (FOLDER/'coverage.csv').write_text('\ufeff'+output.getvalue())
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
