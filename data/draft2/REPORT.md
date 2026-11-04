# Concert Atlas · Draft 2

Baseline report for the original 79 screenshots. After admin uploads, the website and coverage CSV/JSON show the current full catalog, including newer versions; the counts in this baseline report remain historical.

The execution workspace was checked before extraction: the existing four unit tests passed, Python 3.12 and the Flask environment worked, and the checkout had no changes. The repository's `concert-atlas-demo.zip` is the immutable draft-1 baseline. All 79 JPGs in the uploaded `nct wish gocheok.zip` match its source references by SHA-256. Attached screenshot text is treated as supplier evidence, not instructions.

## What this draft contains

**3,568 identified option rows across all 79 screenshots**, with original filenames, source IDs, physical row numbers, original-image bounding boxes, raw OCR, draft-1 OCR references, extraction status, and structured fields where readable. There are **175 original visual transcriptions and 3,393 OCR candidates**. None of the identified row bands is left without text evidence, but many structured fields remain uncertain. These are source offers, not a count of unique or available tickets. Row ranges and seat alternatives remain grouped, and repeated/updated screenshots remain separate.

Coverage means every *identified table row* is represented. It does **not** mean all fields have been visually checked. OCR can misread, split, merge, or miss characters; some captured numeric or section values may still be wrong. The original row crop and full screenshot remain the authority. Selected fields in `field-review.json` were checked visually in this draft, without upgrading an entire row to fully verified.

## Unresolved fields

- Section not parsed: **122 rows**.
- Row not parsed: **0 rows**.
- Seat not parsed / not supplied: **276 rows**.
- Year or date unresolved: **1,167 rows**.
- Numeric quote unresolved (excluding explicitly sold rows): **12 rows**.

These counts measure explicit gaps, not all possible OCR errors. Yearless January dates remain unresolved; literal November dates are retained. Printed 2026 dates remain 2026 even when other sheets show 2027. No year is inferred from a screenshot filename or update date. Original masked seat strings are retained; `2X` is not a quantity of two. The inherited one-per-row convention is provisional, and grouped offers require confirmation.

Color alone is retained as a marking, not treated as proof of sale. The explicit green/paid and yellow/locked legend in the 197-series sheets is recorded separately. Explicit sold text is retained. Quotes remain supplier quotes in CNY; customer selling prices remain unset. Seller identity, screenshot order and current stock are unknown.

## Open and review

Unzip `concert-atlas-draft2.zip` and open `concert-atlas/index.html`, keeping `source-images/` beside it. No server or network is required. The explorer defaults to all dates; use the extraction-status filter to separate draft-1 visual rows from the review queue. The supplier library contains all 79 sources, a coverage table and CSV download. Each row opens its original-image crop and raw text. Unmapped sections remain reachable in the section dropdown under UNRESOLVED.

Reports included beside the app:

- `reports/coverage.csv` and `coverage.json`: per-screenshot row counts, visual/OCR split, unresolved-field counts and source hashes.
- `reports/ticket-options.csv`: every source option with uncertainty, raw text and provenance.
- This report and `provenance.json`.

## Reproduce

From `/workspace/ticketing`, run `.venv/bin/python scripts/build_draft2.py`, then `.venv/bin/python scripts/export_demo.py`. The compiler uses the original demo plus retained `data/draft2/row-layouts.json`, `ocr-words.json` and `field-review.json`. It does not require OCR packages to rebuild. The source images and immutable draft-1 demo must stay in place. Rebuilding is deterministic.

## Row corrections and upload support

The missing-row cases were visually rechecked against the originals, including 区/区域, 排/排数, 座位号 and Korean 구역/열. All 3,568 existing options now have a row value; letter rows and alternatives remain intact. `data/row-corrections.json` records 359 selected row/section reviews, and the parser now separates printed listing IDs from seating columns. Remaining uncertain sections and other fields are still labelled. Admin screenshot uploads require one-time free Cloudflare Worker setup; see `docs/ADMIN_UPLOADS.md` in the repository.

## Validation

- Five existing/expanded unit tests passed, including source counts, row bounds, stable draft-1 IDs, duplicates, explicit sold rows, color markings and date conflicts.
- JavaScript syntax validation passed.
- Browser smoke passed: seating selection, keyboard controls, dates, sold filters, details, original images, search, CSV, mobile layout, review queue and coverage.
- Exported static demo passed separately: embedded catalog, row crops, full source images, all 79 coverage records, and coverage CSV. It made no API calls or external requests and had no JavaScript errors.
- ZIP integrity and all 79 bundled source images were checked. Catalog rebuild produced the same SHA-256.
- Direct `file://` navigation could not be tested because this managed Chromium blocks it by administrator policy. The same exported files were validated through a local static server. Opening the portable file directly on a personal computer remains unverified in this workspace.

## Coverage by screenshot

Identified rows and represented rows are equal for each source below. "Visual" refers only to draft-1 full-row transcription; "OCR" includes candidates with selected fields visually checked in draft 2. The full CSV contains unresolved-field counts.

| Source | Screenshot | Identified / represented | Visual | OCR |
| --- | --- | ---: | ---: | ---: |
| 1 | 1731793624205_.pic_hd.jpg | 18 / 18 | 0 | 18 |
| 2 | 1741793624234_.pic.jpg | 25 / 25 | 0 | 25 |
| 3 | 1751793624245_.pic_hd.jpg | 28 / 28 | 28 | 0 |
| 4 | 1761793624261_.pic_hd.jpg | 18 / 18 | 0 | 18 |
| 5 | 1771793624273_.pic.jpg | 31 / 31 | 0 | 31 |
| 6 | 1781793624568_.pic.jpg | 21 / 21 | 0 | 21 |
| 7 | 1801793624648_.pic.jpg | 6 / 6 | 6 | 0 |
| 8 | 1841793625841_.pic_hd.jpg | 156 / 156 | 0 | 156 |
| 9 | 1851793625843_.pic_hd.jpg | 139 / 139 | 0 | 139 |
| 10 | 1861793625979_.pic.jpg | 83 / 83 | 0 | 83 |
| 11 | 1871793625996_.pic_hd.jpg | 8 / 8 | 8 | 0 |
| 12 | 1891793626048_.pic_hd.jpg | 82 / 82 | 0 | 82 |
| 13 | 1901793626128_.pic_hd.jpg | 15 / 15 | 0 | 15 |
| 14 | 1911793626150_.pic.jpg | 24 / 24 | 0 | 24 |
| 15 | 1921793626194_.pic.jpg | 51 / 51 | 0 | 51 |
| 16 | 1941793626228_.pic.jpg | 53 / 53 | 0 | 53 |
| 17 | 1951793626295_.pic.jpg | 11 / 11 | 0 | 11 |
| 18 | 1961793626331_.pic_hd.jpg | 30 / 30 | 0 | 30 |
| 19 | 1971793626353_.pic_hd.jpg | 61 / 61 | 0 | 61 |
| 20 | 1981793626506_.pic.jpg | 25 / 25 | 0 | 25 |
| 21 | 1991793626582_.pic.jpg | 13 / 13 | 0 | 13 |
| 22 | 2011793626601_.pic.jpg | 40 / 40 | 0 | 40 |
| 23 | 2021793626745_.pic.jpg | 10 / 10 | 10 | 0 |
| 24 | 2031793626756_.pic_hd.jpg | 46 / 46 | 0 | 46 |
| 25 | 2041793626764_.pic_hd.jpg | 40 / 40 | 0 | 40 |
| 26 | 2061793627042_.pic.jpg | 36 / 36 | 0 | 36 |
| 27 | 2081793627135_.pic_hd.jpg | 18 / 18 | 0 | 18 |
| 28 | 2111793628430_.pic.jpg | 57 / 57 | 0 | 57 |
| 29 | 2131793629234_.pic.jpg | 57 / 57 | 0 | 57 |
| 30 | 2161793629513_.pic_hd.jpg | 150 / 150 | 0 | 150 |
| 31 | 2171793629519_.pic_hd.jpg | 121 / 121 | 0 | 121 |
| 32 | 2181793629536_.pic.jpg | 13 / 13 | 0 | 13 |
| 33 | 2191793629639_.pic_hd.jpg | 164 / 164 | 0 | 164 |
| 34 | 2201793629640_.pic_hd.jpg | 139 / 139 | 0 | 139 |
| 35 | 2231793630054_.pic.jpg | 52 / 52 | 0 | 52 |
| 36 | 2261793630455_.pic.jpg | 13 / 13 | 0 | 13 |
| 37 | 2281793630915_.pic.jpg | 13 / 13 | 13 | 0 |
| 38 | 2291793630941_.pic.jpg | 18 / 18 | 0 | 18 |
| 39 | 2321793631362_.pic.jpg | 18 / 18 | 0 | 18 |
| 40 | 2331793631945_.pic.jpg | 13 / 13 | 0 | 13 |
| 41 | 2341793631970_.pic.jpg | 69 / 69 | 0 | 69 |
| 42 | 2351793632694_.pic_hd.jpg | 55 / 55 | 0 | 55 |
| 43 | 2361793632712_.pic.jpg | 1 / 1 | 0 | 1 |
| 44 | 2371793632729_.pic_hd.jpg | 32 / 32 | 0 | 32 |
| 45 | 2381793632741_.pic_hd.jpg | 55 / 55 | 0 | 55 |
| 46 | 2391793633261_.pic_hd.jpg | 8 / 8 | 8 | 0 |
| 47 | 2401793633307_.pic_hd.jpg | 18 / 18 | 0 | 18 |
| 48 | 2411793633628_.pic_hd.jpg | 29 / 29 | 0 | 29 |
| 49 | 2441793635872_.pic.jpg | 164 / 164 | 0 | 164 |
| 50 | 2451793635879_.pic.jpg | 139 / 139 | 0 | 139 |
| 51 | 2461793636275_.pic_hd.jpg | 57 / 57 | 0 | 57 |
| 52 | 2471793636468_.pic_hd.jpg | 10 / 10 | 0 | 10 |
| 53 | 2481793636469_.pic_hd.jpg | 14 / 14 | 0 | 14 |
| 54 | 2491793636471_.pic_hd.jpg | 21 / 21 | 0 | 21 |
| 55 | 2501793638494_.pic.jpg | 27 / 27 | 0 | 27 |
| 56 | 2511793638530_.pic_hd.jpg | 28 / 28 | 0 | 28 |
| 57 | 2521793639980_.pic_hd.jpg | 67 / 67 | 0 | 67 |
| 58 | 2531793640306_.pic_hd.jpg | 26 / 26 | 0 | 26 |
| 59 | 2541793640682_.pic_hd.jpg | 39 / 39 | 39 | 0 |
| 60 | 2571793641553_.pic_hd.jpg | 47 / 47 | 0 | 47 |
| 61 | 2581793642890_.pic.jpg | 47 / 47 | 0 | 47 |
| 62 | 2601793643654_.pic.jpg | 11 / 11 | 11 | 0 |
| 63 | 2611793677903_.pic_hd.jpg | 123 / 123 | 0 | 123 |
| 64 | 2621793677909_.pic_hd.jpg | 96 / 96 | 0 | 96 |
| 65 | 2631793677920_.pic.jpg | 12 / 12 | 0 | 12 |
| 66 | 2651793677957_.pic.jpg | 17 / 17 | 0 | 17 |
| 67 | 2661793677971_.pic_hd.jpg | 48 / 48 | 0 | 48 |
| 68 | 2671793677984_.pic_hd.jpg | 41 / 41 | 0 | 41 |
| 69 | 2681793678003_.pic_hd.jpg | 41 / 41 | 0 | 41 |
| 70 | 2691793678019_.pic_hd.jpg | 44 / 44 | 0 | 44 |
| 71 | 2701793678027_.pic_hd.jpg | 44 / 44 | 0 | 44 |
| 72 | 2711793678077_.pic.jpg | 22 / 22 | 0 | 22 |
| 73 | 2731793687928_.pic.jpg | 20 / 20 | 0 | 20 |
| 74 | 2741793688419_.pic.jpg | 94 / 94 | 0 | 94 |
| 75 | 2761793688508_.pic.jpg | 22 / 22 | 0 | 22 |
| 76 | 2781793688755_.pic.jpg | 11 / 11 | 11 | 0 |
| 77 | 2791793688977_.pic.jpg | 28 / 28 | 28 | 0 |
| 78 | 2801793690017_.pic.jpg | 12 / 12 | 0 | 12 |
| 79 | 2811793693070_.pic.jpg | 13 / 13 | 13 | 0 |
