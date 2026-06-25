ALTER TABLE translation_jobs
    ADD COLUMN IF NOT EXISTS review_status TEXT NOT NULL DEFAULT 'pending_signer_review',
    ADD COLUMN IF NOT EXISTS risk_domains TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS source_ids TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS fallback_count INTEGER NOT NULL DEFAULT 0 CHECK (fallback_count >= 0),
    ADD COLUMN IF NOT EXISTS unknown_token_count INTEGER NOT NULL DEFAULT 0 CHECK (unknown_token_count >= 0);

CREATE INDEX IF NOT EXISTS idx_jobs_review_status_created
    ON translation_jobs(review_status, created_at DESC);
