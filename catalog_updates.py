"""Apply explicitly reviewed screenshot versions; never reconcile tickets by masked seats."""
import copy
import json
from pathlib import Path

def refresh_coverage(catalog):
    coverage=[]
    for source in catalog['sources']:
        rows=[t for t in catalog['tickets'] if t['source_index']==source['source_index']]
        values=dict(physical_option_rows=len(rows),extracted_rows=len(rows),visually_transcribed_rows=sum(t.get('extraction_status')=='visually_transcribed_draft1' for t in rows),ocr_candidate_rows=sum(t.get('extraction_status')=='ocr_candidate' for t in rows),admin_reviewed_rows=sum(t.get('extraction_status')=='admin_reviewed' for t in rows),unreadable_rows=sum(t.get('extraction_status')=='unreadable_row' for t in rows),unresolved_section_rows=sum(t.get('section')=='UNRESOLVED' for t in rows),unresolved_row_rows=sum(not t.get('row') for t in rows),unresolved_seat_rows=sum(not t.get('seat_as_printed') for t in rows),unresolved_date_rows=sum(not t.get('performance_date') for t in rows),unresolved_quote_rows=sum(t.get('price') is None and not t.get('sold') for t in rows))
        source.update(values)
        coverage.append({key:source.get(key) for key in ['source_index','source_file','sha256','visual_family','coverage_status','superseded_by',*values]})
    catalog['coverage']=coverage
    catalog['extraction_summary'].update(total_source_images=len(catalog['sources']),total_option_rows=len(catalog['tickets']),visually_transcribed_rows=sum(c['visually_transcribed_rows'] for c in coverage),ocr_candidate_rows=sum(c['ocr_candidate_rows'] for c in coverage),unreadable_rows=sum(c['unreadable_rows'] for c in coverage),admin_reviewed_rows=sum(c['admin_reviewed_rows'] for c in coverage))
    return catalog

def apply_patch(catalog,patch):
    result=copy.deepcopy(catalog)
    if patch['job_id'] in result.get('applied_updates',[]):return result
    source=patch['source'];base_id=patch.get('base_source_index')
    amendment=patch.get('amend_source_index')
    if amendment is not None:
        previous=next((s for s in result['sources'] if s['source_index']==amendment),None)
        if previous is None or previous['sha256']!=source['sha256'] or source['source_index']!=amendment:
            raise ValueError('Amendment must retain the original source and checksum')
        if previous.get('superseded_by'):raise ValueError('Amend the current source version instead')
        result['sources']=[copy.deepcopy(source) if s['source_index']==amendment else s for s in result['sources']]
        result['tickets']=[t for t in result['tickets'] if t['source_index']!=amendment]+copy.deepcopy(patch['tickets'])
        for reference in patch.get('additional_previous_sources',[]):
            previous=next((s for s in result['sources'] if s['source_index']==reference['source_index']),None)
            if previous is None or previous['sha256']!=reference['sha256']:raise ValueError('Previous snapshot checksum mismatch')
            if previous.get('superseded_by'):raise ValueError('Previous snapshot already has a newer version')
            previous['superseded_by']=source['source_index']
            for ticket in result['tickets']:
                if ticket['source_index']==previous['source_index']:ticket['superseded_by']=source['source_index']
        result.setdefault('applied_updates',[]).append(patch['job_id'])
        return refresh_coverage(result)
    if any(s['sha256']==source['sha256'] for s in result['sources']):raise ValueError('Exact duplicate screenshot already published')
    if any(s['source_index']==source['source_index'] for s in result['sources']):raise ValueError('Source ID already exists')
    if base_id is not None:
        previous=next((s for s in result['sources'] if s['source_index']==base_id),None)
        if previous is None or previous['sha256']!=patch['base_source_sha256']:raise ValueError('Original source changed; choose the current source and review again')
        if previous.get('superseded_by'):raise ValueError('This source already has a newer version; update the latest version instead')
        previous['superseded_by']=source['source_index']
        for ticket in result['tickets']:
            if ticket['source_index']==base_id:ticket['superseded_by']=source['source_index']
    # Curated batch imports may explicitly identify several older snapshots of one sheet.
    for reference in patch.get('additional_previous_sources',[]):
        previous=next((s for s in result['sources'] if s['source_index']==reference['source_index']),None)
        if previous is None or previous['sha256']!=reference['sha256']:raise ValueError('Previous snapshot checksum mismatch')
        if previous.get('superseded_by'):raise ValueError('Previous snapshot already has a newer version')
        previous['superseded_by']=source['source_index']
        for ticket in result['tickets']:
            if ticket['source_index']==previous['source_index']:ticket['superseded_by']=source['source_index']
    result['sources'].append(copy.deepcopy(source));result['tickets'].extend(copy.deepcopy(patch['tickets']))
    result.setdefault('applied_updates',[]).append(patch['job_id'])
    return refresh_coverage(result)

def apply_saved_updates(catalog,directory):
    patches=[json.loads(p.read_text()) for p in Path(directory).glob('*.json')]
    for patch in sorted(patches,key=lambda p:(p['source']['source_index'],p['job_id'])):catalog=apply_patch(catalog,patch)
    return catalog

def write_reports(catalog,root):
    import csv,io
    for name,rows in [('coverage',catalog['coverage']),('ticket-options',catalog['tickets'])]:
        keys=list(dict.fromkeys(k for row in rows for k in row))
        output=io.StringIO();writer=csv.DictWriter(output,fieldnames=keys,lineterminator='\n');writer.writeheader()
        for row in rows:
            clean={}
            for key,value in row.items():
                if isinstance(value,(list,dict)):value=json.dumps(value,ensure_ascii=False)
                if isinstance(value,str) and value.startswith(('=','+','-','@')):value="'"+value
                clean[key]=value
            writer.writerow(clean)
        (Path(root)/f'data/draft2/{name}.csv').write_text('\ufeff'+output.getvalue())
