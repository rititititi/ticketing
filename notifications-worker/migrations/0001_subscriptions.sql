-- Private Cloudflare D1 only. Do not export real subscriber data into this repository.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS pending_subscriptions (
  token_hash TEXT PRIMARY KEY, contact TEXT NOT NULL, contact_hash TEXT NOT NULL,
  preferences TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY, contact TEXT NOT NULL UNIQUE, preferences TEXT NOT NULL,
  confirmed_at INTEGER NOT NULL, last_sent_at INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS alert_events (
  id TEXT PRIMARY KEY, payload TEXT NOT NULL, first_seen_at INTEGER NOT NULL,
  last_seen_at INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS current_alerts ON alert_events(active,first_seen_at);
CREATE TABLE IF NOT EXISTS deliveries (
  subscriber_id TEXT NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
  event_id TEXT NOT NULL, outbox_id TEXT NOT NULL,
  PRIMARY KEY(subscriber_id,event_id)
);
CREATE TABLE IF NOT EXISTS mail_outbox (
  id TEXT PRIMARY KEY, subscriber_id TEXT NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
  payload TEXT NOT NULL, created_at INTEGER NOT NULL, next_attempt_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0, ambiguous INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS subscriber_locks (
  id TEXT PRIMARY KEY, locked_until INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_limits (
  key TEXT PRIMARY KEY,count INTEGER NOT NULL,expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS mail_budget (day TEXT PRIMARY KEY,count INTEGER NOT NULL);
