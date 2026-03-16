-- ============================================================
-- Smart Personal Finance Tracker — PostgreSQL Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name       VARCHAR(255),
    currency        VARCHAR(10)  DEFAULT 'USD',
    monthly_income  NUMERIC(12,2) DEFAULT 0,
    avatar_url      TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ─────────────────────────────────────────
-- CATEGORIES
-- ─────────────────────────────────────────
CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    icon        VARCHAR(50)  DEFAULT '💰',
    color       VARCHAR(20)  DEFAULT '#6366f1',
    type        VARCHAR(20)  CHECK(type IN ('expense','income','both')) DEFAULT 'expense',
    is_system   BOOLEAN DEFAULT FALSE,   -- built-in vs user-created
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_user ON categories(user_id);

-- Seed system categories (user_id NULL = global defaults)
INSERT INTO categories (id, name, icon, color, type, is_system) VALUES
    (uuid_generate_v4(), 'Food & Dining',    '🍔', '#f59e0b', 'expense', TRUE),
    (uuid_generate_v4(), 'Transportation',   '🚗', '#3b82f6', 'expense', TRUE),
    (uuid_generate_v4(), 'Shopping',         '🛍️', '#ec4899', 'expense', TRUE),
    (uuid_generate_v4(), 'Bills & Utilities','⚡', '#8b5cf6', 'expense', TRUE),
    (uuid_generate_v4(), 'Entertainment',    '🎬', '#f43f5e', 'expense', TRUE),
    (uuid_generate_v4(), 'Health & Fitness', '💊', '#10b981', 'expense', TRUE),
    (uuid_generate_v4(), 'Travel',           '✈️', '#06b6d4', 'expense', TRUE),
    (uuid_generate_v4(), 'Education',        '📚', '#6366f1', 'expense', TRUE),
    (uuid_generate_v4(), 'Personal Care',    '💆', '#a855f7', 'expense', TRUE),
    (uuid_generate_v4(), 'Salary',           '💼', '#22c55e', 'income',  TRUE),
    (uuid_generate_v4(), 'Freelance',        '💻', '#84cc16', 'income',  TRUE),
    (uuid_generate_v4(), 'Investment',       '📈', '#14b8a6', 'income',  TRUE),
    (uuid_generate_v4(), 'Other',            '📦', '#94a3b8', 'both',    TRUE);

-- ─────────────────────────────────────────
-- TRANSACTIONS
-- ─────────────────────────────────────────
CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    amount          NUMERIC(12,2) NOT NULL CHECK(amount > 0),
    type            VARCHAR(20) NOT NULL CHECK(type IN ('expense','income')),
    date            DATE NOT NULL,
    tags            TEXT[],
    receipt_url     TEXT,
    is_recurring    BOOLEAN DEFAULT FALSE,
    recurrence_rule VARCHAR(50),   -- 'monthly', 'weekly', 'yearly'
    source          VARCHAR(50) DEFAULT 'manual',  -- 'manual','csv','api'
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user      ON transactions(user_id);
CREATE INDEX idx_transactions_date      ON transactions(date DESC);
CREATE INDEX idx_transactions_category  ON transactions(category_id);
CREATE INDEX idx_transactions_type      ON transactions(type);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date DESC);

-- ─────────────────────────────────────────
-- BUDGETS
-- ─────────────────────────────────────────
CREATE TABLE budgets (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id   UUID REFERENCES categories(id) ON DELETE CASCADE,
    month         SMALLINT NOT NULL CHECK(month BETWEEN 1 AND 12),
    year          SMALLINT NOT NULL,
    amount        NUMERIC(12,2) NOT NULL CHECK(amount >= 0),
    alert_at_pct  SMALLINT DEFAULT 80,  -- alert when X% of budget used
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, category_id, month, year)
);

CREATE INDEX idx_budgets_user       ON budgets(user_id);
CREATE INDEX idx_budgets_user_month ON budgets(user_id, year, month);

-- ─────────────────────────────────────────
-- ANALYTICS SNAPSHOTS  (pre-computed, refreshed nightly)
-- ─────────────────────────────────────────
CREATE TABLE analytics_snapshots (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month                   SMALLINT NOT NULL,
    year                    SMALLINT NOT NULL,
    total_income            NUMERIC(12,2) DEFAULT 0,
    total_expense           NUMERIC(12,2) DEFAULT 0,
    net_savings             NUMERIC(12,2) DEFAULT 0,
    savings_rate            NUMERIC(5,2)  DEFAULT 0,
    financial_health_score  SMALLINT      DEFAULT 0,
    category_breakdown      JSONB,        -- {category_id: amount}
    top_categories          JSONB,        -- [{name, amount, pct}]
    anomalies               JSONB,        -- [{transaction_id, reason, severity}]
    predicted_next_month    NUMERIC(12,2),
    ml_insights             JSONB,        -- free-form AI insights array
    computed_at             TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, year, month)
);

CREATE INDEX idx_analytics_user ON analytics_snapshots(user_id, year DESC, month DESC);

-- ─────────────────────────────────────────
-- REFRESH TRIGGER — updated_at auto-update
-- ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_users_updated        BEFORE UPDATE ON users        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_transactions_updated BEFORE UPDATE ON transactions  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_budgets_updated      BEFORE UPDATE ON budgets       FOR EACH ROW EXECUTE FUNCTION set_updated_at();
