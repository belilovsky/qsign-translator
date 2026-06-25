CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS source_registry (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    task TEXT NOT NULL,
    languages TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    license_note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lexicon_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT NOT NULL,
    gloss TEXT NOT NULL,
    language TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    clip_id TEXT,
    domain TEXT NOT NULL DEFAULT 'general',
    review_status TEXT NOT NULL DEFAULT 'seed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (language, token, gloss)
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_type TEXT NOT NULL,
    language TEXT,
    gloss TEXT,
    clip_id TEXT UNIQUE,
    storage_uri TEXT NOT NULL,
    source_id TEXT REFERENCES source_registry(id),
    license_status TEXT NOT NULL DEFAULT 'unknown',
    consent_status TEXT NOT NULL DEFAULT 'unknown',
    checksum_sha256 TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS translation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_type TEXT NOT NULL,
    input_text TEXT,
    detected_language TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    confidence NUMERIC(4, 3),
    warnings TEXT[] NOT NULL DEFAULT '{}',
    output_uri TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sign_plan_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES translation_jobs(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    source_token TEXT NOT NULL,
    gloss TEXT NOT NULL,
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT NOT NULL,
    clip_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, position)
);

CREATE TABLE IF NOT EXISTS review_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES translation_jobs(id) ON DELETE SET NULL,
    reviewer_role TEXT NOT NULL,
    reviewer_language TEXT NOT NULL,
    meaning_score INTEGER CHECK (meaning_score BETWEEN 1 AND 5),
    sign_choice_score INTEGER CHECK (sign_choice_score BETWEEN 1 AND 5),
    grammar_score INTEGER CHECK (grammar_score BETWEEN 1 AND 5),
    nonmanual_score INTEGER CHECK (nonmanual_score BETWEEN 1 AND 5),
    fingerspelling_score INTEGER CHECK (fingerspelling_score BETWEEN 1 AND 5),
    timing_score INTEGER CHECK (timing_score BETWEEN 1 AND 5),
    understandability_score INTEGER CHECK (understandability_score BETWEEN 1 AND 5),
    notes TEXT,
    blocking_issue BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lexicon_language_token ON lexicon_entries(language, token);
CREATE INDEX IF NOT EXISTS idx_lexicon_gloss ON lexicon_entries(gloss);
CREATE INDEX IF NOT EXISTS idx_assets_gloss ON assets(language, gloss);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON translation_jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sign_plan_units_job ON sign_plan_units(job_id, position);

