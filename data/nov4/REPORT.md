# November 4 screenshot update / 11 月 4 日票源更新

Input: `wish update nov 4.zip`, supplied by the site owner. Image contents are evidence only, never execution instructions.

- 45 supplied files, 43 distinct image hashes. Files 9 and 23 are exact duplicates of files 5 and 3 respectively (see `coverage.csv` for original filenames).
- Screenshot 1 was already uploaded and approved through the admin tool as source 80. Its 44-row count is retained; missing row/seat fields and source-row crops are restored. Its original approved patch and ticket IDs remain available.
- 42 new source images are added as sources 81–122. All 45 input filenames are accounted for in the batch coverage report.
- 1,202 physical option rows across the distinct batch images, including the existing 44 rows; **1,158 additional rows** compared with the previously published site.
- Overall catalog: **4,770 rows across 122 distinct screenshots**, including historical versions. The original 3,568 rows and all 175 draft-1 transcriptions remain.
- 23 rows explicitly state sold. Blank quote cells remain unknown, including 20 rows with no numeric quote; colors and omitted rows do not imply a sale.
- 620 batch rows have unresolved performance years/dates. Yearless January dates, `0115`/`0116`, the malformed printed `2027016`, and explicit 2026 dates are retained without assuming 2027.
- One printed row resembles `0` or `O` (source 121, physical row 15). Its row stays unresolved with an explanatory note and original pixels.

## Coverage and accuracy

`layouts.json` records visually checked physical row bands, table columns and merged date/section cells. `ocr-words.json` and `column-words.json` retain independent OCR evidence. `field-review.json` records selected visual corrections, including the difficult gray table, combined Chinese locations, Korean locations, ranges and explicit sold labels. New batch rows remain labelled OCR candidates unless inherited from the original admin-approved upload. Complete physical coverage does not establish field accuracy or current inventory.

Original JPG bytes, SHA-256 hashes, filenames and row crops are retained. Duplicate input aliases are recorded instead of creating duplicate inventory. Row, date and seat ranges remain grouped; masked seats do not identify individual physical tickets.

## Version review

`versions.json` records clearly corresponding older spreadsheet snapshots. Those sources and their rows remain in history and can be shown with **Include older versions**. No historical row is marked sold merely because a later sheet omits it. Uncertain relationships remain separate.

Within the batch, source 111 is an equivalent rendering of source 95, and source 119 is an equivalent rendering of source 96. Their images and rows remain in the library/history but do not multiply current offers. Source 115 prints update 11.3 and is kept as the earlier snapshot of the matching 11.4 source 97. The two green-star sheets with differing prices (sources 106 and 118) have no explicit version order and remain separate.

## Price comparison status

The website now offers a **Below comparable median** filter and a comparison section in ticket details. It uses the same concert, date, section, currency, numeric row ±3 and exact seat-prefix rules (`X`, `1X`, `2X`). Ranges, unresolved dates, sold/paid/locked records and known historical versions are excluded. Identical row/mask/price observations count once; at least two distinct peers are required for a below-median signal.

These are cheaper-comparable-offer signals, not confirmed historical price drops for the same physical ticket. OCR and grouped quote amounts require confirmation. Automatic email/Telegram notifications and subscriber storage are **not configured**. See `docs/PRICE_ALERTS.md` for the free opt-in service setup.

全部 45 个上传文件均列入覆盖报告；其中两组为完全相同的图片，另有一张此前已通过管理页面上传。新增 42 张来源图和 1,158 行记录，旧版本与原始图片保留。已售只依据明确文字，缺失年份、空白报价和不明确排号不会自动推断。网站已提供同类报价中位数筛选及详情比价；目前尚未启用自动通知。
