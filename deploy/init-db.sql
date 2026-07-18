-- =====================================================================
-- Elite Decision Engine - Production PostgreSQL Schema Initialization
-- =====================================================================
-- This script prepares the database environment on initial deploy.
-- All definitions align exactly with SQLAlchemy ORM mappings in database.py.
-- All statements are fully idempotent (using CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS).

-- ---------------------------------------------------------------------
-- Table: users
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ---------------------------------------------------------------------
-- Table: user_settings
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    dashboard_config JSONB DEFAULT '{}'::jsonb,
    risk_preferences JSONB DEFAULT '{}'::jsonb,
    theme VARCHAR(20) DEFAULT 'dark',
    layout_config JSONB DEFAULT '{}'::jsonb,
    notification_preferences JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ---------------------------------------------------------------------
-- Table: signals
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10),
    timeframe VARCHAR(10),
    divergence VARCHAR(50),
    price DOUBLE PRECISION,
    score DOUBLE PRECISION DEFAULT 0,
    confidence DOUBLE PRECISION DEFAULT 0,
    market_health DOUBLE PRECISION DEFAULT 0,
    btc_health DOUBLE PRECISION DEFAULT 0,
    volume_score DOUBLE PRECISION DEFAULT 0,
    funding_score DOUBLE PRECISION DEFAULT 0,
    oi_score DOUBLE PRECISION DEFAULT 0,
    cvd_score DOUBLE PRECISION DEFAULT 0,
    trend_score DOUBLE PRECISION DEFAULT 0,
    risk_score DOUBLE PRECISION DEFAULT 0,
    approved BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'OPEN',
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);

-- ---------------------------------------------------------------------
-- Table: trades
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER,
    symbol VARCHAR(20),
    side VARCHAR(10),
    entry DOUBLE PRECISION,
    stop DOUBLE PRECISION,
    tp1 DOUBLE PRECISION,
    tp2 DOUBLE PRECISION,
    rr DOUBLE PRECISION,
    pnl DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(30) DEFAULT 'OPEN',
    exit_price DOUBLE PRECISION,
    closed_at TIMESTAMP WITH TIME ZONE,
    close_reason VARCHAR(30),
    exchange_order_id VARCHAR(120),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at DESC);

-- ---------------------------------------------------------------------
-- Table: notifications
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_type VARCHAR(30) NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_event_type ON notifications(event_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- ---------------------------------------------------------------------
-- Table: watchlists
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    name VARCHAR(50) NOT NULL DEFAULT 'Default',
    symbols JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);

-- ---------------------------------------------------------------------
-- Table: journal_entries
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(10),
    entry_price DOUBLE PRECISION,
    exit_price DOUBLE PRECISION,
    score DOUBLE PRECISION DEFAULT 0,
    confidence DOUBLE PRECISION DEFAULT 0,
    entry_reason TEXT,
    exit_reason TEXT,
    notes TEXT,
    result VARCHAR(20) DEFAULT 'PENDING',
    pnl DOUBLE PRECISION DEFAULT 0,
    signal_id INTEGER,
    trade_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_journal_entries_symbol ON journal_entries(symbol);
CREATE INDEX IF NOT EXISTS idx_journal_entries_result ON journal_entries(result);
CREATE INDEX IF NOT EXISTS idx_journal_entries_created_at ON journal_entries(created_at DESC);
