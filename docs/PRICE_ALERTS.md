# Price alerts for uu scout / 价格提醒

The public site now has a **Below comparable median** filter and **Compare similar tickets** in each ticket's details. It compares current offers using the rules below and links to cheaper comparable source records. A below-median signal requires at least two distinct peer quotes. Identical row/mask/price observations are counted once in the benchmark. Browser comparisons use the complete catalog, independently of display filters.

These are comparisons across offers, not historical drops for an identified physical ticket. OCR quotes and per-ticket versus bundle pricing still require confirmation. `pricing.py` contains the same tested eligibility/matching rules. The **New updates** section now shows on-site alerts with a read/unread badge, source evidence and previous-quote links. Read state stays in this browser. No email/Telegram delivery or subscriber database is configured; no external messages have been sent.

网站现已提供“低于同类报价中位数”筛选，并在票源详情中显示“比较相近票源”。中位数提示至少需要两个不同的同类报价；相同排号、掩码和价格的重复记录只计一次。目前比较不同票源，不能确认同一张实体票降价；尚未启用订阅或自动通知。

## Matching rules

Compare only current, unsold offers for the **same concert, performance date, currency and section**. Require a numeric printed row and a parseable seat mask. Include rows within **±3**, inclusive. Match the mask exactly: **1X ↔ 1X, X ↔ X, 2X ↔ 2X**. An annotation such as `1X(3内)` retains the `1X` mask, while ambiguous alternatives such as `X/2X` are excluded. Unknown dates, unresolved sections, letter/range rows, paid/locked source records and superseded versions are excluded from automatic comparisons.

Example: F4, row 12, 1X can be compared with F4, rows 9–15, 1X at the same performance. It cannot be compared with F4 row 12, X or 2X, another date, or row 16.

比较范围：同一演唱会、同一场次日期、同一币种和区域；排数差不超过 3 排；座位掩码严格相同。`1X` 只配 `1X`、`X` 只配 `X`、`2X` 只配 `2X`。暂不自动比较字母排、范围排、未知日期、已售／锁定／已付款或旧版本。`15/16/17` 不应擅自拆成三张票。

## A free notification program

1. Create a free Telegram bot using BotFather. Interested fans opt in by starting the bot and choosing their date, section, row and mask. Store subscriber chat IDs/preferences privately in Cloudflare D1 or KV; never in this public GitHub repository.
2. After each approved upload, run a comparison job. Use `pricing.comparable` to build the relevant peer group. Exclude known older versions and exact duplicates, and confirm whether quotes are per ticket or a bundle before using them.
3. Choose the alert policy: for example, an offer at least **10% below the median** of matching current offers, or a chosen RMB threshold. That is a *cheaper comparable offer*. For a true historical price-drop alert, require a supplier listing ID or an explicitly reviewed link between versions; masked seat attributes alone do not identify a unique physical ticket.
4. Save the previous benchmark and sent-alert keys in private storage. Send each material change once, respecting Telegram rate limits and unsubscribe requests. The message should include the old/new price or benchmark, the comparable rows, performance date, source reference, and a link to the site.
5. Trigger the job after successful publication rather than polling every visitor's browser. Telegram delivery is free; Cloudflare/GitHub quotas still apply.

推荐免费组合：Telegram Bot + 私有 Cloudflare D1/KV 订阅信息 + 发布后的 GitHub Actions 比价任务。粉丝主动订阅并可退订；按“同区、±3 排、同掩码”的规则匹配，再按你选定的折扣／金额门槛提醒。不要将“与类似票源相比更便宜”直接当成“同一张实体票降价”。

Before enabling alerts, decide: Telegram or another channel; percentage/RMB threshold; whether a comparison should use the median or the cheapest current comparable; and how supplier-confirmed listing IDs will be linked between versions. No notifications have been enabled or sent by this change.

## New updates / 最新动态

`updates_feed.py` produces the public feed whenever screenshots or admin reviews are published. The exporter embeds it in the standalone HTML, so GitHub Pages and downloaded ZIPs support the same section without a separate API or sign-up.

- **Price drop in updated listing:** require an explicitly linked screenshot-version relationship, a nonempty explicit printed listing ID (or its retained leading ID/date OCR column), a unique match within each earlier source, and the same resolved date, section, printed numeric row and seat prefix. Compare with the lowest matching earlier quote so differing historical snapshots do not exaggerate a drop. Original and previous ticket links are shown. OCR and physical ticket identity still require supplier confirmation.
- **Lower comparable offer:** require at least two distinct peer row/price observations under the existing ±3-row matching rules. Repeat observations do not multiply the benchmark, and repeat identical offer observations appear once in the feed. This is not described as a historical drop for the same physical ticket.
- Sold, paid, locked, known older versions and unresolved dates/ranges/masks do not enter the feed. Records disappear from the current alerts if subsequent publication makes them ineligible.
- Stable alert IDs preserve read state across reloads; changed quotes/benchmarks produce different IDs. Read state is stored only in `localStorage` on the current browser. This is not a private user account or email subscription.

“最新动态”现已展示网页内提醒、未读数量及前后报价证据。提醒随发布更新，已读状态保存在本浏览器。未来可增加邮件或 Telegram 主动订阅、验证及退订，届时需私有订阅信息存储与发送服务；目前暂未启用。

## Email subscription implementation

The private email Worker and public signup tab are now implemented. Email confirmation, watchlist matching, publication-triggered delivery, retries and unsubscribe are covered by tests. Live sending remains off until sender verification and private service configuration are completed. See [NOTIFICATIONS.md](NOTIFICATIONS.md). Earlier descriptions of subscriber storage as unimplemented refer to the initial comparison-only version. Telegram remains a future option.
