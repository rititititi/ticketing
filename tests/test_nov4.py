import copy,hashlib,json,unittest
from pathlib import Path
from catalog_updates import apply_patch
ROOT=Path(__file__).resolve().parents[1]
class Nov4Tests(unittest.TestCase):
    def test_every_input_and_physical_row_is_accounted_for(self):
        report=json.loads((ROOT/'data/nov4/coverage.json').read_text());catalog=json.loads((ROOT/'data/catalog.json').read_text());sources={s['source_index']:s for s in catalog['sources']}
        self.assertEqual(len(report),45);self.assertEqual(len({r['sha256'] for r in report}),43)
        self.assertEqual({r['screenshot']:r['duplicate_of'] for r in report if r['duplicate_of']},{9:5,23:3})
        self.assertEqual(sum(r['physical_option_rows'] for r in report if not r['duplicate_of']),1202)
        self.assertEqual(len({r['source_index'] for r in report}),43)
        for record in report:
            source=sources[record['source_index']]
            self.assertEqual(hashlib.sha256((ROOT/'static/sources'/source['source_file']).read_bytes()).hexdigest(),record['sha256'])
            self.assertEqual(source['physical_option_rows'],record['physical_option_rows'])
        # Original extraction evidence stays immutable when an admin later corrects fields.
        rows=[t for p in (ROOT/'data/updates').glob('nov4-*.json') for t in json.loads(p.read_text())['tickets']]
        self.assertTrue({t['id'] for t in rows}.issubset({t['id'] for t in catalog['tickets']}))
        self.assertEqual(len(rows),1202);self.assertEqual(sum(t['sold'] for t in rows),23)
        self.assertEqual(sum(not t['performance_date'] for t in rows),620)
        unknown=[t for t in rows if not t['row']];self.assertEqual([(t['source_index'],t['physical_row']) for t in unknown],[(121,15)])
        self.assertTrue(all(t['source_bbox'] for t in rows))
        self.assertTrue(all(t['price'] is None for t in rows if t['sold']))
    def test_amendment_is_checked_and_keeps_original_approved_record(self):
        original=json.loads((ROOT/'data/updates/8475020773ee4ea3a7639e82b58ce85f.json').read_text())
        amendment=next(json.loads(p.read_text()) for p in (ROOT/'data/updates').glob('nov4-*.json') if json.loads(p.read_text()).get('amend_source_index')==80)
        self.assertEqual([t['id'] for t in original['tickets']],[t['id'] for t in amendment['tickets']])
        catalog=json.loads((ROOT/'data/catalog.json').read_text());bad=copy.deepcopy(amendment);bad['job_id']='invalid-amendment';bad['source']['sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'checksum'):apply_patch(catalog,bad)
        bad=copy.deepcopy(amendment);bad['job_id']='invalid-amendment';bad['additional_previous_sources'][0]['sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'checksum'):apply_patch(catalog,bad)
        self.assertEqual(apply_patch(catalog,amendment),catalog)
