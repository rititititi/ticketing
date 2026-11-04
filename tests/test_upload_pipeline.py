import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from catalog_updates import apply_patch,apply_saved_updates
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('process_screenshot',ROOT/'scripts/process_screenshot.py');processor=importlib.util.module_from_spec(spec);spec.loader.exec_module(processor)

class UploadPipelineTests(unittest.TestCase):
    def test_review_required_version_preserved_and_idempotent(self):
        base=json.loads((ROOT/'data/catalog.json').read_text());next_index=max(s['source_index'] for s in base['sources'])+1
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job='a'*32;folder=root/'data/upload-jobs'/job;folder.mkdir(parents=True);(root/'data/draft2').mkdir();(root/'data/catalog.json').write_text(json.dumps(base))
            image=b'test image bytes; publishing does not rerun OCR';(folder/'input.jpg').write_bytes(image)
            old=base['sources'][0]
            request=dict(id=job,extension='jpg',input_path=f'data/upload-jobs/{job}/input.jpg',sha256=hashlib.sha256(image).hexdigest(),base_source_index=1,base_source_sha256=old['sha256'])
            (folder/'request.json').write_text(json.dumps(request))
            rows=[dict(section='F4',row='12',seat_as_printed='1X',performance_date='2027-01-15',price=3500,sold=False,notes='',raw_ocr='F4区12排1X 3500'),dict(section='F4',row='13',seat_as_printed='2X',performance_date='2027-01-15',price=4000,sold=True,notes='',raw_ocr='F4区13排2X SOLD')]
            review=dict(status='review',reviewed_all_rows=False,rows=rows,width=600,height=800)
            (folder/'review.json').write_text(json.dumps(review))
            with self.assertRaisesRegex(ValueError,'approval required'):processor.publish(root,job)
            self.assertEqual(json.loads((root/'data/catalog.json').read_text()),base)
            review.update(status='approved',reviewed_all_rows=True);(folder/'review.json').write_text(json.dumps(review));processor.publish(root,job)
            updated=json.loads((root/'data/catalog.json').read_text())
            self.assertEqual(len(updated['sources']),len(base['sources'])+1)
            self.assertEqual(len(updated['tickets']),len(base['tickets'])+2)
            self.assertEqual(updated['sources'][0]['superseded_by'],next_index)
            historical=[t for t in updated['tickets'] if t['source_index']==1]
            self.assertTrue(all(t['superseded_by']==next_index for t in historical))
            self.assertEqual([t['sold'] for t in historical],[t['sold'] for t in base['tickets'] if t['source_index']==1])
            self.assertTrue(updated['tickets'][-1]['sold']);self.assertIsNone(updated['tickets'][-1]['price'])
            self.assertEqual(apply_saved_updates(base,root/'data/updates'),updated)
            processor.publish(root,job)
            self.assertEqual(json.loads((root/'data/catalog.json').read_text()),updated)
            patch=json.loads((root/'data/updates'/f'{job}.json').read_text());patch['job_id']='b'*32
            with self.assertRaisesRegex(ValueError,'duplicate'):apply_patch(updated,patch)
            stale=copy.deepcopy(patch);stale['source']['source_index']=next_index+1;stale['source']['sha256']='new'
            with self.assertRaisesRegex(ValueError,'newer version'):apply_patch(updated,stale)
    def test_validator_keeps_ranges_but_rejects_invalid_dates_and_prices(self):
        row=dict(section='F4',row='15/16/17',seat_as_printed='X',performance_date='',price=4000,sold=False,notes='',raw_ocr='')
        self.assertEqual(processor.validate_rows([row])[0]['row'],'15/16/17')
        for change in [dict(price=float('nan')),dict(price=True),dict(performance_date='2027-02-30'),dict(sold='yes'),dict(section='T99')]:
            with self.assertRaises(ValueError):processor.validate_rows([{**row,**change}])
