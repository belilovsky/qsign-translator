ALTER TABLE translation_jobs
    ADD COLUMN IF NOT EXISTS publish_status TEXT NOT NULL DEFAULT 'draft';

CREATE INDEX IF NOT EXISTS idx_jobs_publish_status_created
    ON translation_jobs(publish_status, created_at DESC);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES translation_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor_role TEXT NOT NULL DEFAULT 'system',
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_job_created
    ON audit_events(job_id, created_at DESC);
