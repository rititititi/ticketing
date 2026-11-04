# Price alerts for uu scout / 价格提醒

The public site now has a **Below comparable median** filter and **Compare similar tickets** in each ticket's details. It compares current offers using the rules below and links to cheaper comparable source records. A below-median signal requires at least two distinct peer quotes. Identical row/mask/price observations are counted once in the benchmark. Browser comparisons use the complete catalog, independently of display filters.

These are comparisons across offers, not historical drops for an identified physical ticket. OCR quotes and per-ticket versus bundle pricing still require confirmation. `pricing.py` contains the same tested eligibility/matching rules. No notification service, subscriber database or Telegram delivery is configured; no alerts have been sent.

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
