# Email ticket alerts / 邮件票源提醒

**Implementation status:** the signup, confirmation, matching, delivery queue and unsubscribe flow are implemented. **Live sending is off until the private service and verified sender are configured.** No real subscriber addresses or credentials belong in this public repository.

The website remains on free GitHub Pages. A separate **uu-scout-notifications** Cloudflare Worker uses a private free-plan D1 database and Brevo's transactional email API. You can start Brevo's sender verification using an existing email address; complete any account/sender checks Brevo requests before enabling delivery. If your account requires additional domain verification, an approved sending identity is needed before fan email can go live. The code does not bypass sender rules or activate a paid plan. Resend is also supported for a future verified-domain sender.

## Decisions in this version

- **Email first.** No Telegram subscription or delivery is active.
- Send when **new matching updates are published**, rather than a daily newsletter. Publications trigger the Worker; a five-minute cron retries queued work and catches missed triggers. Email arrival is subject to the provider and free-service scheduling.
- Fans choose the **performance date, section, numeric printed row and exact seat prefix**. Match the same performance and section within **±3 rows**, with `X` only matching `X`, `1X` only `1X`, and so on. Letter/range rows and unresolved dates are excluded.
- Fans choose price drops in linked listings, lower comparable offers, or both. Their **minimum percentage** applies to either type (default 10%, configurable in the form).
- **One watchlist per email.** A newly confirmed signup replaces the prior watchlist. Changing preferences requires email confirmation again.
- Confirmation is mandatory before activation. Links expire after **24 hours**. Opening a link alone does not activate or unsubscribe: an explicit button press is required, so mail-security scanners cannot perform those actions.
- Existing deals form the baseline at confirmation. They are **not** sent as new alerts. New event IDs from subsequent publications can trigger mail. A single email summarizes up to ten matching records, links to the site, and reports the total matching count.
- Every alert links to unsubscribe. Unsubscribe removes email, preferences and queued mail from the private subscription database, even when sending is paused. The email provider may retain its own delivery logs under its retention policy.
- Trial hard cap: **100 active subscriptions** (a lower cap can be configured), **250 attempted emails/day**, including confirmation emails. Keep the configured cap below your provider's actual free allowance. A full list or exhausted budget does not falsely activate a signup.

## Activate the free services

### 1. Verify an email sender

1. Create a free Brevo account and complete its account checks.
2. In **Senders, Domains & Dedicated IPs → Senders**, add a sender named **uu scout** with your existing email address. Follow the verification email and any additional sender instructions. No purchase is made by this code.
3. In **SMTP & API → API Keys**, generate an **API key**, not an SMTP password. Keep it private. Do not paste it into chat, source files or GitHub public variables.

### 2. Create the private database

In Cloudflare, create a free D1 database named `uu-scout-notifications`. Apply the SQL in [0001_subscriptions.sql](../notifications-worker/migrations/0001_subscriptions.sql), either through its Console or Wrangler.

The CLI version, using your existing Cloudflare login:

```sh
npx wrangler d1 create uu-scout-notifications
```

Copy the returned **database ID** into the commented D1 binding in [wrangler.toml](../notifications-worker/wrangler.toml), uncomment that block, then run:

```sh
npx wrangler d1 migrations apply uu-scout-notifications --remote --config notifications-worker/wrangler.toml
```

The database ID is configuration, not a credential, and can be committed. **The real database contents must never be exported into this repository.** Keep the binding in `wrangler.toml` so future Git deployments retain it.

### 3. Deploy the notifications Worker

Connect the same GitHub repo to another Cloudflare Worker project. Use:

```sh
npx wrangler deploy --config notifications-worker/wrangler.toml
```

Use **uu-scout-notifications**, separate from the existing admin Worker. No root-directory setting is needed.

In the notifications Worker's settings add **Secrets**:

| Name | Value |
| --- | --- |
| `BREVO_API_KEY` | Brevo API key |
| `TOKEN_SECRET` | At least 32 random characters from your password manager |
| `PUBLISH_SECRET` | A different random value of at least 32 characters |

Add these **variables**:

| Name | Value |
| --- | --- |
| `FROM_EMAIL` | Your provider-verified sender email address |
| `PUBLIC_URL` | This Worker's actual HTTPS URL, with no trailing slash |
| `EMAIL_ENABLED` | `true`, only after sender verification is complete |

`EMAIL_PROVIDER=brevo`, `SITE_URL`, `FEED_URL`, the trial limits and the cron schedule are already in the config. `keep_vars=true` preserves dashboard-only variables on later deployments. Do not commit a sender email or credential just to configure it. If you choose a different Worker name/subdomain, update `PUBLIC_URL` in the config as well.

### 4. Connect the website and publication trigger

In the GitHub repo's **Settings → Secrets and variables → Actions** add:

- **Variable** `UU_SCOUT_NOTIFICATIONS_URL`: the notifications Worker's HTTPS URL.
- **Secret** `NOTIFICATIONS_PUBLISH_SECRET`: the same private value as the Worker's `PUBLISH_SECRET`.

Then run **Actions → Publish uu scout → Run workflow → main**. Changing a repository variable alone does not rebuild an already deployed site. Use the latest **main**, not the earlier `d6db4ea` screenshot-import commit.

The Email alerts form enables only when the Worker reports readiness. Test confirmation in your own inbox before sharing the signup link with fans. Provider errors are shown as failures rather than a fake success. There is no automatic sender purchase, paid upgrade, or external message sent by the local tests.

## How fans sign up

1. Open **Email alerts** on the website (`#notifications`).
2. Enter an email and choose date, section, printed row, seat prefix, alert types and minimum discount.
3. Tick the explicit email-alert consent box and press **Send confirmation email**.
4. Open the email (also check spam), follow its link, and press **Confirm email alerts**. Only then is the subscription active.
5. New matching published alerts are emailed automatically. Each includes ticket details, source references, comparison context, the website link and unsubscribe.

The website never stores the email in browser storage or in the public GitHub catalog. Confirmation/unsubscribe pages have no third-party analytics and use a no-referrer policy. Credentials remain in Worker Secrets. Subscription and delivery data are private D1 records.

## Delivery behavior and limits

The private publication endpoint requires `PUBLISH_SECRET`; it cannot be used anonymously to send campaigns. Signup has per-IP and per-recipient rate limits, bounded requests, consent, a honeypot, and confirmation. Unsubscribe uses a signed token and works without the sender API being available.

Per-subscriber leases, durable event claims and a private outbox prevent concurrent runs from mailing the same event twice. Provider calls carry stable idempotency keys. Known failures are retried with backoff; an uncertain delivery is not retried after the provider's deduplication window, preventing accidental duplicate mail. `uncertain`/`failed` outbox rows need operator inspection if delivery troubleshooting is required. Long runs stop within the Worker execution window; remaining work is picked up by the retry schedule. Free-provider quotas can delay or stop delivery.

Unconfirmed signups expire after 24 hours and are cleaned up on a delivery run. Sent/failed outbox content is removed after 30 days; provider logs are governed separately. Unsubscribe immediately deletes the subscriber and cascades its outbox/delivery claims.

本版本先做邮件提醒：粉丝选择场次、区域、数字排号及相同座位号前缀，按上下 3 排匹配；确认邮箱后，在新的匹配动态发布时收到提醒。每封邮件有退订入口。邮箱和偏好仅保存在私有 D1 数据库，不存入公开 GitHub 仓库。发送仍需完成 Brevo 发件人审核、Cloudflare D1 绑定及密钥配置；未完成时，网站会明确显示“正在设置”，不会假装订阅成功。无需自动购买域名或升级付费方案。
