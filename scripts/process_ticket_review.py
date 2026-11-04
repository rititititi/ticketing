"""Publish explicitly approved row/seat/stock corrections; never execute screenshot text."""
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ticket_reviews import apply_review,validate_changes
from catalog_updates import write_reports
from updates_feed import write_derived

def publish(root,job):
    if not re.fullmatch('[a-f0-9]{32}',job):raise ValueError('Invalid review job ID')
    folder=root/'data/review-jobs'/job;request=json.loads((folder/'request.json').read_text())
    if request.get('id')!=job:raise ValueError('Review job reference mismatch')
    if (folder/'result.json').exists() and json.loads((folder/'result.json').read_text()).get('status')=='published':return
    catalog=json.loads((root/'data/catalog.json').read_text())
    updated=apply_review(catalog,request)
    originals={t['id']:t for t in catalog['tickets']};after={t['id']:t for t in updated['tickets']}
    review={**request,'audit':[dict(id=c['id'],before={k:originals[c['id']].get(k) for k in ['row','seat_as_printed','availability','sold','price']},after={k:after[c['id']].get(k) for k in ['row','seat_as_printed','availability','sold','price']}) for c in request['changes']]}
    (root/'data/reviews').mkdir(parents=True,exist_ok=True);(root/'data/reviews'/f'{job}.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
    (root/'data/catalog.json').write_text(json.dumps(updated,ensure_ascii=False,separators=(',',':')))
    (root/'data/draft2/coverage.json').write_text(json.dumps(updated['coverage'],ensure_ascii=False,indent=2));write_reports(updated,root);write_derived(updated,root)
    (folder/'result.json').write_text(json.dumps(dict(status='published',id=job,reviewed_count=len(request['changes']),message='Approved corrections saved; website deployment is starting'),ensure_ascii=False,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);args=parser.parse_args()
    if not re.fullmatch('[a-f0-9]{32}',args.job):raise ValueError('Invalid review job ID')
    try:publish(ROOT,args.job)
    except Exception as error:
        (ROOT/'data/review-jobs'/args.job/'result.json').write_text(json.dumps(dict(status='failed',error=str(error)),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
