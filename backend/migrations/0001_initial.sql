-- Market Scout initial schema (Supabase Postgres + pgvector).
-- Apply via Supabase SQL editor, supabase CLI, or the Supabase MCP `apply_migration` tool.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed system user (id=0) referenced by PortfolioInsight when no auth context exists.
INSERT INTO users (id, email)
VALUES (0, 'system@marketscout.local')
ON CONFLICT (id) DO NOTHING;
SELECT setval(pg_get_serial_sequence('users', 'id'), GREATEST((SELECT MAX(id) FROM users), 1));

CREATE TABLE IF NOT EXISTS queries (
    id          UUID PRIMARY KEY,
    request     TEXT NOT NULL,
    company     VARCHAR(255) NOT NULL,
    ticker      VARCHAR(32)  NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_queries_ticker ON queries(ticker);

CREATE TABLE IF NOT EXISTS reports (
    id          UUID PRIMARY KEY,
    query_id    UUID NOT NULL REFERENCES queries(id),
    company     VARCHAR(255) NOT NULL,
    ticker      VARCHAR(32)  NOT NULL,
    report_path TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_reports_ticker  ON reports(ticker);
CREATE INDEX IF NOT EXISTS ix_reports_company ON reports(company);

CREATE TABLE IF NOT EXISTS report_data (
    report_id      UUID PRIMARY KEY REFERENCES reports(id) ON DELETE CASCADE,
    company_info   JSONB,
    financial_data JSONB,
    risk_data      JSONB,
    news_data      JSONB,
    analysis       JSONB
);

CREATE TABLE IF NOT EXISTS portfolio (
    ticker         VARCHAR(32) PRIMARY KEY,
    shares         DOUBLE PRECISION NOT NULL,
    purchase_price DOUBLE PRECISION,
    company_name   VARCHAR(255),
    holding_id     VARCHAR(64),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolio_insights (
    id                 SERIAL PRIMARY KEY,
    user_id            INTEGER NOT NULL DEFAULT 0 REFERENCES users(id),
    portfolio_metadata JSONB,
    insight_text       TEXT NOT NULL,
    embedding          vector(1536) NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_portfolio_insights_user ON portfolio_insights(user_id);

-- HNSW vector index — fast cosine similarity over the embedding column.
CREATE INDEX IF NOT EXISTS ix_portfolio_insights_embedding_hnsw
    ON portfolio_insights
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
