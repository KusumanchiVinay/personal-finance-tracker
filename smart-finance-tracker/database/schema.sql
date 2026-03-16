-- ============================================================
-- Smart Personal Finance Tracker — PostgreSQL Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── USERS ───────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    currency        VARCHAR(10) DEFAULT 'USD',
    monthly_income  NUMERIC(14,2) DEFAULT 0,
    avatar_url      TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ─── CATEGORIES ──────────────────────────────────────────────
CREATE TABLE categories (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    icon       VARCHAR(50) DEFAULT '💰',
    color      VARCHAR(7) DEFAULT '#6366f1',
    type       VARCHAR(20) CHECK (type IN ('expense','income')) DEFAULT 'expense',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_user ON categories(user_id);

-- Seed default categories (applied per user via trigger or seeder)
INSERT INTO categories (id, user_id, name, icon, color, type, is_default) VALUES
    (uuid_generate_v4(), NULL, 'Food & Dining',    '🍔', '#f59e0b', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Transportation',   '🚗', '#3b82f6', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Shopping',         '🛍️', '#ec4899', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Bills & Utilities','⚡', '#8b5cf6', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Entertainment',    '🎬', '#f97316', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Health & Fitness', '💊', '#10b981', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Travel',           '✈️', '#06b6d4', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Education',        '📚', '#84cc16', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Housing',          '🏠', '#78716c', 'expense', TRUE),
    (uuid_generate_v4(), NULL, 'Salary',           '💼', '#22c55e', 'income',  TRUE),
    (uuid_generate_v4(), NULL, 'Freelance',        '💻', '#a3e635', 'income',  TRUE),
    (uuid_generate_v4(), NULL, 'Investment',       '📈', '#34d399', 'income',  TRUE),
    (uuid_generate_v4(), NULL, 'Other',            '📦', '#94a3b8', 'expense', TRUE);

-- ─── TRANSACTIONS ─────────────────────────────────────────────
CREATE TABLE transactions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id   UUID REFERENCES categories(id) ON DELETE SET NULL,
    amount        NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    type          VARCHAR(20) CHECK (type IN ('expense','income')) NOT NULL,
    description   TEXT,
    merchant      VARCHAR(255),
    date          DATE NOT NULL DEFAULT CURRENT_DATE,
    is_recurring  BOOLEAN DEFAULT FALSE,
    recur_period  VARCHAR(20) CHECK (recur_period IN ('daily','weekly','monthly','yearly')),
    tags          TEXT[] DEFAULT '{}',
    note          TEXT,
    is_anomaly    BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(5,4),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user        ON transactions(user_id);
CREATE INDEX idx_transactions_date        ON transactions(date DESC);
CREATE INDEX idx_transactions_category    ON transactions(category_id);
CREATE INDEX idx_transactions_user_date   ON transactions(user_id, date DESC);
CREATE INDEX idx_transactions_type        ON transactions(user_id, type);

-- ─── BUDGETS ──────────────────────────────────────────────────
CREATE TABLE budgets (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    amount      NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    period      VARCHAR(20) CHECK (period IN ('monthly','yearly')) DEFAULT 'monthly',
    month       INTEGER CHECK (month BETWEEN 1 AND 12),
    year        INTEGER CHECK (year >= 2020),
    alert_at    NUMERIC(5,2) DEFAULT 80.00, -- alert at 80% usage
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, category_id, period, month, year)
);

CREATE INDEX idx_budgets_user ON budgets(user_id);

-- ─── AI ANALYTICS ─────────────────────────────────────────────
CREATE TABLE analytics_cache (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type         VARCHAR(50) NOT NULL,   -- 'health_score','prediction','anomaly','suggestion'
    payload      JSONB NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at   TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',
    UNIQUE (user_id, type)
);

CREATE INDEX idx_analytics_user_type ON analytics_cache(user_id, type);
CREATE INDEX idx_analytics_expires   ON analytics_cache(expires_at);

-- ─── REFRESH TOKEN STORE ──────────────────────────────────────
CREATE TABLE refresh_tokens (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);

-- ─── AUDIT LOG ────────────────────────────────────────────────
CREATE TABLE audit_log (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID REFERENCES users(id) ON DELETE SET NULL,
    action     VARCHAR(100) NOT NULL,
    entity     VARCHAR(50),
    entity_id  UUID,
    old_data   JSONB,
    new_data   JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── TRIGGERS ────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at        BEFORE UPDATE ON users        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_budgets_updated_at      BEFORE UPDATE ON budgets      FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── VIEWS ───────────────────────────────────────────────────
CREATE VIEW v_monthly_summary AS
SELECT
    t.user_id,
    DATE_TRUNC('month', t.date)::DATE AS month,
    t.type,
    c.name AS category,
    COUNT(*) AS tx_count,
    SUM(t.amount) AS total
FROM transactions t
LEFT JOIN categories c ON c.id = t.category_id
GROUP BY t.user_id, DATE_TRUNC('month', t.date), t.type, c.name;

CREATE VIEW v_category_budget_status AS
SELECT
    b.user_id,
    b.category_id,
    c.name AS category_name,
    c.icon,
    b.amount AS budget_amount,
    b.month,
    b.year,
    COALESCE(SUM(t.amount), 0) AS spent,
    ROUND(COALESCE(SUM(t.amount), 0) / NULLIF(b.amount, 0) * 100, 2) AS pct_used
FROM budgets b
JOIN categories c ON c.id = b.category_id
LEFT JOIN transactions t ON
    t.user_id       = b.user_id AND
    t.category_id   = b.category_id AND
    t.type          = 'expense' AND
    EXTRACT(MONTH FROM t.date) = b.month AND
    EXTRACT(YEAR  FROM t.date) = b.year
GROUP BY b.user_id, b.category_id, c.name, c.icon, b.amount, b.month, b.year;
