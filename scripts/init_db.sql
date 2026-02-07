-- Learning Context: single row storing user's learning goals
CREATE TABLE IF NOT EXISTS learning_context (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    goals TEXT NOT NULL DEFAULT '',
    digest_format TEXT NOT NULL DEFAULT 'daily',
    methodology JSONB NOT NULL DEFAULT '{"style": "practical", "depth": "intermediate", "consumption": "30min"}',
    skill_levels JSONB NOT NULL DEFAULT '{}',
    time_availability TEXT NOT NULL DEFAULT '30 minutes per day',
    project_context TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed the single row
INSERT INTO learning_context (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

-- Learning Context History: snapshots on every update
CREATE TABLE IF NOT EXISTS learning_context_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot JSONB NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Digest Items: scored content items per digest run
CREATE TABLE IF NOT EXISTS digest_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    content_snippet TEXT NOT NULL DEFAULT '',
    score NUMERIC(3, 1) NOT NULL DEFAULT 0.0,
    justification TEXT NOT NULL DEFAULT '',
    included_in_email BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (url, digest_date)
);

CREATE INDEX IF NOT EXISTS idx_digest_items_date ON digest_items (digest_date);
CREATE INDEX IF NOT EXISTS idx_digest_items_score ON digest_items (digest_date, score DESC);

-- Feedback: user responses to digest items
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES digest_items (id) ON DELETE CASCADE,
    response TEXT NOT NULL CHECK (response IN ('useful', 'not_useful')),
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_item ON feedback (item_id);

-- Digest Log: pipeline run tracking
CREATE TABLE IF NOT EXISTS digest_log (
    digest_date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    status TEXT NOT NULL DEFAULT 'running',
    items_ingested INTEGER NOT NULL DEFAULT 0,
    items_scored INTEGER NOT NULL DEFAULT 0,
    items_emailed INTEGER NOT NULL DEFAULT 0,
    precision_rate NUMERIC(5, 2),
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);
