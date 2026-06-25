ALTER TABLE translation_jobs
    ADD COLUMN IF NOT EXISTS output_kind TEXT NOT NULL DEFAULT 'sign_plan_preview',
    ADD COLUMN IF NOT EXISTS output_status TEXT NOT NULL DEFAULT 'not_rendered',
    ADD COLUMN IF NOT EXISTS render_adapter TEXT;

CREATE INDEX IF NOT EXISTS idx_jobs_output_status_created
    ON translation_jobs(output_status, created_at DESC);
