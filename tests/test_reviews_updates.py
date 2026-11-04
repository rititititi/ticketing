import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from ticket_reviews import validate_changes,apply_review,apply_saved_reviews,fingerprint,review_reasons,write_review_index
from updates_feed import build_feed
ROOT=Path(__file__).resolve().parents[1]
def ticket(id='new',**changes):
    return dict(id=id,event_id='wish',concert='wish',source_index=2,source_file='new.jpg',physical_row=1,source_row='physical-1',source_bbox=[0,20,600,40],section='F4',row='12',seat_as_printed='1X',performance_date='2027-01-15',price=3000,supplier_quote_cny=3000,currency='CNY',sold=False,availability='unconfirmed_source_option',raw_ocr='1 | 20270115 | F4 12 1X 3000',printed_identifier='1',extraction_status='ocr_candidate',batch_id='2026-11-04',**changes)
def sample():
    t=ticket();return dict(sources=[dict(source_index=2,source_file='new.jpg',sha256='source-hash',width=600,height=800)],tickets=[t],extraction_summary={})
def request(catalog,**changes):
    t=catalog['tickets'][0]
    return dict(id='a'*32,source_index=2,source_sha256='source-hash',confirmed=True,approved_at='2026-11-04T08:00:00Z',changes=[dict(id=t['id'],revision=fingerprint(t),row='13',seat_as_printed='2X',availability='available',note='Checked original',**changes)])
class ReviewTests(unittest.TestCase):
    def test_review_is_audited_replayable_and_does_not_promote_other_fields(self):
        base=sample();review=request(base);updated=apply_review(base,review);t=updated['tickets'][0]
        self.assertEqual((t['row'],t['seat_as_printed'],t['availability']),('13','2X','admin_confirmed_available'))
        self.assertEqual(t['extraction_status'],'ocr_candidate');self.assertEqual(t['price'],3000)
        self.assertTrue(t['catalog_review']['row_confirmed']);self.assertEqual(review_reasons(t),[])
        self.assertEqual(base['tickets'][0]['row'],'12');self.assertEqual(apply_review(updated,review),updated)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'review.json').write_text(json.dumps(review));self.assertEqual(apply_saved_reviews(base,p),updated)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_review_index(updated,root);index=json.loads((root/'data/admin-review/index.json').read_text());self.assertEqual(index['total_pending'],0)
    def test_chinese_row_numbers_are_normalized_and_invalid_numerals_rejected(self):
        review=request(sample());review['changes'][0]['row']='十一'
        self.assertEqual(validate_changes(review['changes'])[0]['row'],'11')
        review['changes'][0]['row']='一二'
        with self.assertRaises(ValueError):validate_changes(review['changes'])

    def test_stale_source_record_and_wrong_source_are_rejected_atomically(self):
        base=sample();review=request(base);before=copy.deepcopy(base)
        for mutation in ['revision','source','historical','id','confirm','row']:
            bad=copy.deepcopy(review);catalog=copy.deepcopy(base)
            if mutation=='revision':bad['changes'][0]['revision']='0'*64
            elif mutation=='source':bad['source_sha256']='stale'
            elif mutation=='historical':catalog['sources'][0]['superseded_by']=3
            elif mutation=='id':bad['changes'][0]['id']='other'
            elif mutation=='confirm':bad['confirmed']=False
            else:bad['changes'][0]['row']='price 3000'
            with self.assertRaises(ValueError):apply_review(catalog,bad)
        self.assertEqual(base,before)
    def test_unknown_stays_pending_and_sold_can_restore_only_a_known_quote(self):
        base=sample();review=request(base);review['changes'][0].update(row='',seat_as_printed='',availability='unknown')
        t=apply_review(base,review)['tickets'][0];self.assertEqual(review_reasons(t),['row_missing','seat_missing','availability_unknown'])
        review=request(base);review['changes'][0]['availability']='sold';sold=apply_review(base,review);self.assertTrue(sold['tickets'][0]['sold']);self.assertIsNone(sold['tickets'][0]['price']);self.assertEqual(sold['tickets'][0]['last_listed_price'],3000)
        back=request(sold);back['id']='b'*32;restored=apply_review(sold,back);self.assertFalse(restored['tickets'][0]['sold']);self.assertEqual(restored['tickets'][0]['price'],3000)
    def test_publication_job_records_before_after_and_survives_rebuild(self):
        spec=importlib.util.spec_from_file_location('review_job',ROOT/'scripts/process_ticket_review.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=sample();req=request(base);folder=root/'data/review-jobs'/req['id'];folder.mkdir(parents=True);(root/'data/draft2').mkdir();(root/'data/catalog.json').write_text(json.dumps(base));(folder/'request.json').write_text(json.dumps(req));module.publish(root,req['id'])
            result=json.loads((folder/'result.json').read_text());self.assertEqual(result['status'],'published')
            audit=json.loads((root/'data/reviews'/f"{req['id']}.json").read_text());self.assertEqual(audit['audit'][0]['before']['row'],'12');self.assertEqual(audit['audit'][0]['after']['row'],'13')
            updated=json.loads((root/'data/catalog.json').read_text());self.assertEqual(apply_saved_reviews(base,root/'data/reviews'),updated);module.publish(root,req['id'])
class FeedTests(unittest.TestCase):
    def test_drop_requires_linked_version_unique_listing_and_matching_attributes(self):
        base=sample();old=ticket('old');old.update(source_index=1,source_file='old.jpg',price=4000,superseded_by=2)
        base['tickets'].append(old);base['sources'].append(dict(source_index=1,source_file='old.jpg',sha256='old',superseded_by=2))
        feed=build_feed(base);self.assertEqual(feed['counts']['listing_drop'],1);e=feed['events'][0];self.assertEqual((e['previous_price'],e['price'],e['percent']),(4000,3000,25))
        old['seat_as_printed']='2X';self.assertEqual(build_feed(base)['counts']['listing_drop'],0)
        old['seat_as_printed']='1X';base['sources'][-1].pop('superseded_by');self.assertEqual(build_feed(base)['counts']['listing_drop'],0)
    def test_comparable_alerts_deduplicate_and_exclude_ineligible_quotes(self):
        base=sample()
        for id,row,price in [('peer1','10',4000),('peer-copy','10',4000),('peer2','15',5000)]:
            peer=ticket(id);peer.update(row=row,price=price);base['tickets'].append(peer)
        sold=ticket('sold');sold.update(sold=True,price=100);base['tickets'].append(sold)
        feed=build_feed(base);event=next(e for e in feed['events'] if e['ticket_id']=='new');self.assertEqual(event['kind'],'below_median');self.assertEqual(event['median'],4500);self.assertEqual(event['peer_count'],2)
        self.assertEqual(build_feed(base),feed)
        base['tickets'][0]['performance_date']=None;self.assertFalse(any(e['ticket_id']=='new' for e in build_feed(base)['events']))
