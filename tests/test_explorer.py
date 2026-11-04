import json
import unittest
from pathlib import Path
from app import app

ROOT=Path(__file__).resolve().parents[1]
class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
    def test_page_and_assets(self):
        for url in ['/', '/explore', '/uploads/', '/static/explorer.css', '/static/explorer.js', '/static/i18n.js']:
            with self.client.get(url) as response:
                self.assertEqual(response.status_code,200,url)
    def test_all_source_evidence_retained(self):
        response=self.client.get('/api/catalog')
        self.assertEqual(response.status_code,200)
        data=response.get_json()
        self.assertEqual(len([t for t in data['tickets'] if t['source_index']<=79]),3568)
        self.assertEqual(data['draft_version'],2)
        self.assertGreaterEqual(len(data['sources']),122)
        self.assertEqual(len(data['ocr']),4042)
        self.assertEqual(len({t['id'] for t in data['tickets']}),len(data['tickets']))
        for source in data['sources']:
            self.assertTrue((ROOT/'static/sources'/source['source_file']).is_file())
    def test_draft2_coverage_and_provenance(self):
        data=self.client.get('/api/catalog').get_json()
        self.assertEqual(len(data['coverage']),len(data['sources']))
        self.assertEqual(sum(s['extracted_rows'] for s in data['coverage']),len(data['tickets']))
        self.assertEqual(sum(s['visually_transcribed_rows'] for s in data['coverage']),175)
        for s in data['sources']:
            rows=[t for t in data['tickets'] if t['source_index']==s['source_index']]
            self.assertEqual(len(rows),s['physical_option_rows'])
            self.assertEqual([t['physical_row'] for t in rows],list(range(1,len(rows)+1)))
            for t in rows:
                self.assertEqual(t['source_file'],s['source_file'])
                if t['source_bbox'] is None:
                    self.assertEqual(t['extraction_status'],'admin_reviewed');continue
                x,y,w,bottom=t['source_bbox']
                self.assertGreaterEqual(y,0)
                self.assertLessEqual(bottom,s['height'])
                self.assertGreater(bottom,y)
                self.assertTrue(t['raw_ocr'] or t['legacy_ocr'])
                self.assertIn(t['extraction_status'],['visually_transcribed_draft1','ocr_candidate','unreadable_row','admin_reviewed'])
        self.assertTrue(all(t['row'] for t in data['tickets'] if t['source_index']<=79))
        self.assertEqual(sum(s['unresolved_row_rows'] for s in data['coverage'] if s['source_index']<=79),0)
        # The black sheet had 18 visible options but zero meaningful OCR in draft 1.
        black=[t for t in data['tickets'] if t['source_index']==4]
        self.assertEqual(len(black),18)
        self.assertEqual(black[0]['price'],5000)
        self.assertTrue(black[4]['sold'])
        # Printed missing years and explicit 2026 years remain distinct.
        yearless=[t for t in data['tickets'] if t['source_index']==1]
        self.assertTrue(all(t['performance_date'] is None for t in yearless))
        dated=[t for t in data['tickets'] if t['source_index']==74]
        self.assertEqual(len(dated),94)
        self.assertTrue(all(t['performance_date'].startswith('2026-') for t in dated))
        self.assertEqual(dated[-1]['row'],'15')
        # Red backgrounds without a sold legend retain numeric quotes and remain uncertain.
        red=[t for t in data['tickets'] if t['source_index']==33 and 'red' in t['source_color_markings']]
        self.assertTrue(red)
        self.assertTrue(any(not t['sold'] for t in red))

    def test_versions_and_dates_are_not_silently_merged(self):
        data=self.client.get('/api/catalog').get_json()
        rows={t['id']:t for t in data['tickets']}
        self.assertEqual(rows['src-62-row-6']['price'],3200)
        self.assertTrue(rows['src-76-row-6']['sold'])
        self.assertFalse(rows['src-62-row-6']['sold'])
        self.assertEqual(rows['src-59-row-NCTWISH-1']['date_key'],'2026-01-15')
        self.assertEqual(rows['src-11-row-1']['date_key'],'unresolved')
        self.assertEqual(rows['src-77-row-13']['price'],3209)
        self.assertTrue(all(t['customer_price_cny'] is None for t in data['tickets']))
    def test_masked_seats_remain_distinct(self):
        rows={t['id']:t for t in self.client.get('/api/catalog').get_json()['tickets']}
        for id in ['src-3-row-24','src-3-row-25']:
            self.assertEqual(rows[id]['seat_as_printed'],'1X')
            self.assertEqual(rows[id]['quantity'],1)

if __name__=='__main__':unittest.main()
