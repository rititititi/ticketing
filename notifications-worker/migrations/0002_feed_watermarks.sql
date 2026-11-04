-- Skip unchanged feeds and subscribers who have already checked the current publication.
ALTER TABLE subscribers ADD COLUMN last_checked_at INTEGER NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS service_state (key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS pending_mail ON mail_outbox(subscriber_id,status,next_attempt_at);
