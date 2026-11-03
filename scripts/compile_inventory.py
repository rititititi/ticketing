"""Compile supplier evidence without deduplicating masked seats or guessing dates."""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def compile_inventory(source):
    checked = json.loads((source / 'checked-source-rows.json').read_text())
    sources = json.loads((source / 'source-index.json').read_text())
    lines = json.loads((source / 'all-ocr-UNVERIFIED.json').read_text())
    tickets = []
    for row in checked:
        item = dict(row)
        item['id'] = f"src-{row['source_index']}-row-{row['source_row']}"
        item['section'] = re.sub(r'^FLOOR\s+', '', row['section']).upper()
        item['date_key'] = row['performance_date'] or 'unresolved'
        item['price'] = row['supplier_quote_cny']
        item['sold'] = row['availability'] == 'sold_out_in_source'
        # A source row is evidence, not a unique ticket or a confirmed offer.
        item['status'] = 'Sold in this source' if item['sold'] else 'Supplier confirmation needed'
        tickets.append(item)
    catalog = {'concert': 'NCT WISH', 'venue': 'Gocheok Sky Dome · Seoul',
               'currency': 'CNY', 'tickets': tickets, 'sources': sources,
               'ocr': lines, 'draft': True}
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')))
    for s in sources:
        shutil.copy2(source/s['image_link'], ROOT/'static/sources'/s['source_file'])
    print(f"Compiled {len(tickets)} checked source rows, {len(sources)} images, {len(lines)} unverified OCR lines. No inventory merged or published.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('review_directory', type=Path)
    compile_inventory(parser.parse_args().review_directory)
