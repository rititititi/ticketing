# November 5 screenshot update

Eight uploaded files accounted for: seven ticket spreadsheets add 211 option rows; one unrelated vocabulary screenshot is excluded. The catalog now preserves 4,981 rows across 129 source screenshots, including history.

| Screenshot | File | Source | Rows | Explicitly sold |
| --- | --- | --- | --- | --- |
| 1 | 12651793849966_.pic.jpg | 123 | 9 | 0 |
| 2 | 12611793809455_.pic.jpg | 124 | 85 | 51 |
| 3 | 12671793852047_.pic.jpg | 125 | 6 | 0 |
| 4 | 12661793850086_.pic.jpg | 126 | 40 | 2 |
| 5 | 12641793849962_.pic_hd.jpg | 127 | 21 | 0 |
| 6 | 12591793808459_.pic.jpg | 128 | 32 | 0 |
| 7 | 12601793809424_.pic.jpg | Excluded: vocabulary | 0 | 0 |
| 8 | 12631793849928_.pic_hd.jpg | 129 | 18 | 0 |

All ticket-table row boundaries were visually checked; cached Chinese/English OCR and selected visual transcriptions are retained with row crops and SHA-256 source references. Coverage is separate from field accuracy and supplier confirmation. All section and row fields are represented. Source 127 updates source 105, using the same header, labelled columns and retained printed listing IDs; the earlier snapshot remains in history. Other sources have no positively established predecessor.

53 rows explicitly say SOLD or 售出. Missing rows, green/red backgrounds and slash prices do not establish sold status. Eight slash prices remain unresolved. Source 128 displays `2E+07` in its date cells; no exact date is inferred. Sources 124, 126 and 129 omit the year, which remains unresolved. Source 123 explicitly prints 2027 in its title. Source 129 omits seat numbers on its first 17 rows. Seat ranges and the printed `1n/2n` notation in source 125 remain verbatim. Uncertain fields stay in admin review, and unresolved dates/seats do not generate matching price alerts.

Reproduction: `python scripts/import_nov5.py` (requires original images under artifacts/nov5) followed by `python scripts/build_draft2.py`. Saved patches replay from the repository without OCR or the uploaded ZIP. See coverage.json / coverage.csv for every input and field gaps.
