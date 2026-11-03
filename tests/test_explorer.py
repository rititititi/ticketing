import json
import unittest
from pathlib import Path
from app import app

ROOT=Path(__file__).resolve().parents[1]
class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
    def test_page_and_assets(self):
        for url in ['/', '/explore', '/static/explorer.css', '/static/explorer.js']:
            with self.client.get(url) as response:
                self.assertEqual(response.status_code,200,url)
    def test_all_source_evidence_retained(self):
        response=self.client.get('/api/catalog')
        self.assertEqual(response.status_code,200)
        data=response.get_json()
        self.assertEqual(len(data['tickets']),175)
        self.assertEqual(len(data['sources']),79)
        self.assertEqual(len(data['ocr']),4042)
        self.assertEqual(len({t['id'] for t in data['tickets']}),175)
        for source in data['sources']:
            self.assertTrue((ROOT/'static/sources'/source['source_file']).is_file())
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
