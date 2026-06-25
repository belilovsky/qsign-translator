CREATE TABLE IF NOT EXISTS feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES translation_jobs(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL CHECK (
        feedback_type IN ('good', 'wrong_sign', 'unclear_sign', 'missing_sign', 'offensive')
    ),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_events_job_created
    ON feedback_events(job_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_events_type_created
    ON feedback_events(feedback_type, created_at DESC);
