CREATE TABLE IF NOT EXISTS lexicon_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES translation_jobs(id) ON DELETE CASCADE,
    unit_position INTEGER NOT NULL CHECK (unit_position >= 1),
    source_token TEXT NOT NULL,
    suggested_gloss TEXT NOT NULL,
    suggested_language TEXT NOT NULL,
    suggested_clip_id TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (
        status IN ('open', 'accepted', 'rejected', 'applied')
    ),
    created_by_role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lexicon_suggestions_job_created
    ON lexicon_suggestions(job_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_lexicon_suggestions_status_created
    ON lexicon_suggestions(status, created_at DESC);
