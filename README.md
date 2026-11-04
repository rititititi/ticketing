# uu scout · NCT WISH Gocheok

English / 简体中文 fan ticket explorer. [Download the latest uu scout ZIP](https://github.com/rititititi/ticketing/raw/refs/heads/main/uu-scout.zip).

To make the website available to fans, follow [the bilingual GitHub Pages sharing guide](SHARING.md). The repository includes the **Publish uu scout** deployment workflow. The website URL after deployment is `https://rititititi.github.io/ticketing/`.


## Screenshot uploads and row corrections

The Chinese/Korean parser now separates 区/区域, 排/排数 and 座位号 and supports letter rows and row alternatives. The original missing-row cases were visually rechecked; all 3,568 existing options now have a row value. Selected row/section corrections are recorded in `data/row-corrections.json`; remaining uncertain sections and other fields stay labelled.

The new **Admin uploads / 管理上传** section connects to the free Cloudflare Worker admin panel. It requires one-time activation and private Worker secrets: [bilingual setup and usage guide](docs/ADMIN_UPLOADS.md). Uploads require review before publishing. Updated screenshots retain older versions, and sold status is explicit.

[Price alert matching rules and a free Telegram implementation plan](docs/PRICE_ALERTS.md). The matcher is implemented and tested; subscriber storage and notifications are not enabled.

## Draft 2

[Download Concert Atlas draft 2](https://github.com/rititititi/ticketing/raw/refs/heads/main/concert-atlas-draft2.zip). Unzip it and open `concert-atlas/index.html`; keep `source-images/` beside it.

Draft 2 represents 3,568 identified option rows across all 79 source screenshots. The original 175 visual transcriptions are preserved; 3,393 additional rows are OCR candidates that require field review. Original-image row crops, raw text and per-screenshot coverage are available in the app. See [the draft 2 coverage and limitations report](data/draft2/REPORT.md).

Rebuild the catalog with `.venv/bin/python scripts/build_draft2.py`, then export with `.venv/bin/python scripts/export_demo.py`. The portable result is `artifacts/uu-scout.zip`, including all images and coverage/option CSV reports. The tracked `concert-atlas-demo.zip` remains the immutable draft-1 baseline.

## Try the original interactive demo

Download `concert-atlas-demo.zip` from this repository, unzip it, and open
`concert-atlas/index.html` on your Mac. No Python installation is needed for
the portable demo. Keep its `source-images` folder beside `index.html`.


A local, read-only concert inventory workspace for NCT WISH at Gocheok Sky Dome.
Choose a performance and click the seating schematic to see supplier quote ranges,
source ticket records, seating notes, delivery details and original screenshots.
The supplier library searches all 79 original images and their extracted text.

## Run

Requires Python 3.12 or newer.

```sh
cd /workspace/ticketing
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

The development server listens on port 5000 on the local machine. Open it using
your development environment's supported app viewer. Public hosting uses the static GitHub Pages workflow in [SHARING.md](SHARING.md).
No external fonts, JavaScript CDNs, API keys or third-party services are required.

## Data and limitations

- `data/catalog.json` contains 3,568 source option rows, including 175 original
  visual transcriptions, all 79 source records, and 4,042 original OCR lines.
  The extraction-status filter separates checked rows from OCR candidates.
  Missing fields stay unresolved, and OCR candidates can contain incorrect values.
- Supplier quotes are RMB/CNY. Customer selling prices remain unset.
- Records are **not unique or confirmed stock**. Versions and identical masked
  seats stay separate. The app does not infer update order or seller identity.
- `2X` remains a masked seat number; one ticket per row is the default, not two.
- Sold-in-source records are hidden initially and available via a checkbox.
- Dates printed as 2026 remain 2026. Missing years and conflicting November dates
  are under “Date / year needs review”, not assigned to January 2027.
- The SVG follows the supplied section layout approximately. It is not an official
  seat-level map. No individual seat position is inferred from a masked number.
- This is a fan-facing, read-only ticket explorer. The GitHub Pages export has no
  payment integration or checkout. Original source references and uncertainty
  labels stay available to visitors.
- The earlier booking/import server scaffold is not part of this explorer's
  verified workflow; its admin pages and checkout are not linked in this UI.

## Refresh compiled evidence

Given a review pack containing `checked-source-rows.json`, `source-index.json`,
`all-ocr-UNVERIFIED.json` and `source-images/`:

```sh
python scripts/compile_inventory.py /path/to/extracted-review-pack
```

This rebuilds the catalog and copies the original source images. It does not OCR
new uploads, publish listings, reconcile versions or infer missing dates. Review
new extraction results first. Restart the server if its Python code changes;
refresh the browser after changing data.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
node --check static/explorer.js
```

Browser checks (host Python with Playwright and `/usr/bin/chromium`,
with the app running):

```sh
python tests/browser_smoke.py
python tests/browser_language.py
```

The browser checks exercise section clicks and keyboard selection, date and sold
filters, ticket details, original source images, source search, CSV export and
mobile overflow. Screenshots are written to ignored `artifacts/`.

## Portable browser demo

```sh
python scripts/export_demo.py
```

Unzip `artifacts/uu-scout.zip` and open `uu-scout/index.html` in a
browser. Keep its source-images directory alongside it. This includes the same source quotes, original screenshots, and uncertainty
labels as the app. See [SHARING.md](SHARING.md) for publishing and sharing.
