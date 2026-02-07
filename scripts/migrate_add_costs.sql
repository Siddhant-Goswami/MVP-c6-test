-- Migration: Add cost tracking columns to digest_log
ALTER TABLE digest_log ADD COLUMN IF NOT EXISTS cost_openai_usd NUMERIC(8,4) DEFAULT 0;
ALTER TABLE digest_log ADD COLUMN IF NOT EXISTS cost_apify_usd NUMERIC(8,4) DEFAULT 0;
ALTER TABLE digest_log ADD COLUMN IF NOT EXISTS cost_resend_usd NUMERIC(8,4) DEFAULT 0;
ALTER TABLE digest_log ADD COLUMN IF NOT EXISTS cost_total_usd NUMERIC(8,4) DEFAULT 0;
ALTER TABLE digest_log ADD COLUMN IF NOT EXISTS openai_tokens_used INTEGER DEFAULT 0;
