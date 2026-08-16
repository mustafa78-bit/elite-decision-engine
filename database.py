import logging
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

from config import DATABASE_URL, MAX_SIGNAL_RETRIES, SIGNAL_RETRY_BACKOFF_SECONDS

logger = logging.getLogger(__name__)

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=not _is_sqlite,
    pool_size=1 if _is_sqlite else 10,
    max_overflow=0 if _is_sqlite else 20,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        # WAL lets readers proceed while a writer holds the write lock
        # (default rollback-journal mode blocks readers during a write);
        # busy_timeout makes a writer wait instead of raising
        # "database is locked" immediately when the DB is briefly busy.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# ------------------------------------------------------------------
# SIGNAL TABLE
# ------------------------------------------------------------------

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)

    # Nullable: signals created by background jobs (the scanner, via
    # services/signal_generator.py) have no request context and thus no
    # owning user to stamp -- callers filter with
    # or_(Signal.user_id == user_id, Signal.user_id.is_(None)), same
    # NULL-fallback idiom as services/notification_service.py's
    # _owned_by(). No ForeignKey, matching every other user_id column in
    # this file (Notification, UserSettings, Watchlist) -- established
    # convention here, unlike Trade.signal_id's real FK.
    user_id = Column(Integer, nullable=True, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10))
    timeframe = Column(String(10))
    divergence = Column(String(50))

    price = Column(Float)

    score = Column(Float, default=0)
    confidence = Column(Float, default=0)

    market_health = Column(Float, default=0)
    btc_health = Column(Float, default=0)

    volume_score = Column(Float, default=0)
    funding_score = Column(Float, default=0)
    oi_score = Column(Float, default=0)
    cvd_score = Column(Float, default=0)
    trend_score = Column(Float, default=0)
    risk_score = Column(Float, default=0)

    approved = Column(Boolean, default=False)

    status = Column(String(30), default="OPEN")

    reason = Column(Text)

    # Retry/backoff for transient processing failures (a network blip, a
    # momentary DB error) in DecisionEngine.process_signal() -- distinct
    # from a deliberate REJECTED verdict from the decision pipeline or risk
    # manager, which never touches these columns. See
    # SPRINT_JULES_SIGNAL_RETRY_BACKOFF.md for the full design rationale.
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

# ------------------------------------------------------------------
# TRADE TABLE
# ------------------------------------------------------------------

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)

    # Nullable, no ForeignKey -- same convention as Signal.user_id. Stamped
    # from the parent Signal.user_id at creation time where available (see
    # execution/paper_executor.py), left None otherwise (NULL-fallback
    # filter, same idiom as Signal/Notification).
    user_id = Column(Integer, nullable=True, index=True)

    symbol = Column(String(20))
    side = Column(String(10))

    entry = Column(Float)
    stop = Column(Float)

    tp1 = Column(Float)
    tp2 = Column(Float)

    rr = Column(Float)

    pnl = Column(Float, default=0)

    status = Column(String(30), default="OPEN")

    exit_price = Column(Float)

    closed_at = Column(DateTime(timezone=True))

    close_reason = Column(String(30))

    exchange_order_id = Column(String(120))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# USER TABLE
# ------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# REFRESH TOKEN TABLE
# ------------------------------------------------------------------

class RefreshToken(Base):
    """A long-lived, rotatable credential separate from the short-lived
    JWT access token -- see auth/service.py for the rotation + reuse-
    detection logic this table exists to support. Stores a SHA-256 hash
    of the token, never the raw value, matching this app's existing
    password-hashing hygiene.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    # Always created for a specific, known user at login/register/refresh
    # time -- unlike Signal/Trade/Notification's nullable user_id (which
    # can be background-job-created with no owner), a RefreshToken never
    # exists without one. No ForeignKey, matching this file's other
    # always-owned column (UserSettings.user_id).
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------------
# USER SETTINGS TABLE
# ------------------------------------------------------------------

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    timezone = Column(String(50), default="UTC")
    dashboard_config = Column(JSON, default=dict)
    risk_preferences = Column(JSON, default=dict)
    theme = Column(String(20), default="dark")
    layout_config = Column(JSON, default=dict)
    notification_preferences = Column(JSON, default=dict)


# ------------------------------------------------------------------
# NOTIFICATION TABLE
# ------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(30), nullable=False, index=True)
    payload = Column(JSON, default=dict)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ------------------------------------------------------------------
# WATCHLIST TABLE
# ------------------------------------------------------------------

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    name = Column(String(50), nullable=False, default="Default")
    symbols = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# TEMPORARY WATCH TABLE
# ------------------------------------------------------------------
# Manually-fed, auto-expiring symbols the founder adds from their own
# external analysis -- distinct from Watchlist above (no expiry concept)
# and from scanner/watchlist.py's in-memory WatchlistEngine (no persistence).
# Feeds scanner/core.py's OpportunityScanner alongside FIXED_COIN_UNIVERSE.

class TemporaryWatch(Base):
    __tablename__ = "temporary_watches"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    note = Column(String(255), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)


# ------------------------------------------------------------------
# SENT ALERT TABLE (Telegram news/VC-funding dedup)
# ------------------------------------------------------------------
# Tracks which RSS headlines have already triggered a proactive Telegram
# alert, keyed by category + a normalized hash of the headline text, so the
# periodic news job (services/news_job_service.py) never resends the same
# item across poll cycles even after a backend restart.

class SentAlert(Base):
    __tablename__ = "sent_alerts"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(30), nullable=False, index=True)  # "market_news" | "vc_funding_news"
    headline_hash = Column(String(64), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


# ------------------------------------------------------------------
# JOURNAL ENTRY TABLE
# ------------------------------------------------------------------

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)

    # Nullable: entries created via TradeMemory.record() as a side effect of
    # PaperExecutor.open_trade() inherit the trade's user_id (may itself be
    # None for a manual paper trade with no signal); entries created
    # directly via POST /journal always have a real user_id stamped by the
    # route. Same NULL-fallback filter convention as Signal/Trade.
    user_id = Column(Integer, nullable=True, index=True)

    symbol = Column(String(20), index=True)
    side = Column(String(10))
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)

    score = Column(Float, default=0)
    confidence = Column(Float, default=0)

    entry_reason = Column(Text)
    exit_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    result = Column(String(20), default="PENDING")
    pnl = Column(Float, default=0)

    signal_id = Column(Integer, nullable=True)
    trade_id = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# PAPER ORDER TABLE
# ------------------------------------------------------------------

class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable, no ForeignKey -- same convention as Signal/Trade.user_id.
    user_id = Column(Integer, nullable=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), default="MARKET")
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    filled_price = Column(Float, nullable=True)
    filled_quantity = Column(Float, nullable=True)
    status = Column(String(20), default="PENDING")
    trade_id = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# PAPER TRADE TABLE
# ------------------------------------------------------------------

class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable, no ForeignKey -- same convention as Signal/Trade.user_id.
    user_id = Column(Integer, nullable=True, index=True)
    position_id = Column(Integer, nullable=False)
    order_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, default=0)
    status = Column(String(20), default="OPEN")
    close_reason = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


# ------------------------------------------------------------------
# DECISION EXPLANATION TABLE
# ------------------------------------------------------------------


class DecisionExplanation(Base):
    __tablename__ = "decision_explanations"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)

    decision = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)

    reasons = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    supporting_signals = Column(JSON, default=list)
    risk_notes = Column(JSON, default=list)

    summary = Column(Text, default="")

    technical_score = Column(Float, default=0.0)
    whale_score = Column(Float, default=0.0)
    news_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)

    portfolio_total_equity = Column(Float, default=0.0)
    portfolio_unrealized_pnl = Column(Float, default=0.0)
    portfolio_realized_pnl = Column(Float, default=0.0)
    portfolio_exposure = Column(Float, default=0.0)

    performance_sharpe = Column(Float, default=0.0)
    performance_sortino = Column(Float, default=0.0)
    performance_calmar = Column(Float, default=0.0)
    performance_profit_factor = Column(Float, default=0.0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# COMMANDER MEMORY ENTRY TABLE
# ------------------------------------------------------------------


class CommanderMemoryEntry(Base):
    __tablename__ = "commander_memory"

    id = Column(Integer, primary_key=True, index=True)
    entry_type = Column(String(30), nullable=False, index=True)  # BRIEFING, RECOMMENDATION, PREFERENCE
    key = Column(String(100), nullable=True, index=True)         # preference key, briefing kind
    value = Column(Text, nullable=True)                          # preference value, briefing text, recommendation response_text
    room = Column(String(50), nullable=True)                     # recommendation room
    query = Column(Text, nullable=True)                          # recommendation query
    timestamp = Column(String(100), nullable=True)               # ISO timestamp string
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# TRADE STATUS CONSTANTS
# ------------------------------------------------------------------

OPEN = "OPEN"
CLOSE = "CLOSE"
TAKE_PROFIT = "TAKE_PROFIT"
STOP_LOSS = "STOP_LOSS"
CANCEL = "CANCEL"
TP_HIT = "TP_HIT"
SL_HIT = "SL_HIT"
CLOSED = "CLOSED"
PENDING = "PENDING"
FILLED = "FILLED"
PARTIALLY_FILLED = "PARTIALLY_FILLED"

ORDER_STATUSES = frozenset({PENDING, FILLED, PARTIALLY_FILLED, CANCEL})
TRADE_STATUSES = frozenset({OPEN, TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})
FINAL_STATUSES = frozenset({TP_HIT, SL_HIT, CLOSED, CANCEL})
ORDER_FINAL_STATUSES = frozenset({FILLED, CANCEL})
TRADE_FINAL_STATUSES = frozenset({TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def get_session():
    return SessionLocal()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """Apply pending Alembic migrations up to head. Idempotent -- a no-op if
    the DB is already at head. This is the real schema-provisioning path for
    the live app (see api/main.py's lifespan()); create_tables() above stays
    only for the legacy app.py/startup.py CLI entrypoint and test fixtures,
    neither of which the production Docker image actually runs.
    """
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def is_alert_sent(category: str, headline_hash: str) -> bool:
    """True if this (category, headline) pair has already been alerted."""
    session = get_session()
    try:
        return (
            session.query(SentAlert)
            .filter(SentAlert.category == category, SentAlert.headline_hash == headline_hash)
            .first()
            is not None
        )
    finally:
        session.close()


def record_sent_alert(category: str, headline_hash: str) -> None:
    """Record that this (category, headline) pair was just alerted."""
    with session_scope() as session:
        session.add(SentAlert(category=category, headline_hash=headline_hash))


# ------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------

if __name__ == "__main__":
    create_tables()
    logger.info("Database initialized successfully.")

def update_signal_status(signal_id, new_status):
    if signal_id is None:
        logger.warning("update_signal_status called with None signal_id")
        return False

    session = get_session()

    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            logger.warning("Signal %s not found for status update", signal_id)
            return False

        signal.status = new_status
        session.commit()
        logger.debug("Signal %s status updated to %s", signal_id, new_status)
        return True

    except Exception as e:
        session.rollback()
        logger.error("Failed to update signal %s status: %s", signal_id, e)
        return False

    finally:
        session.close()


def reap_orphaned_processing_signals():
    """Reset any Signal stuck in PROCESSING back to OPEN so it gets picked
    up again. PROCESSING should only ever be a sub-millisecond transient
    state within a single DecisionEngine.process_signal() call (see
    core/engine.py) -- if any row is still PROCESSING when a fresh process
    starts, the previous process crashed mid-execution and orphaned it.
    Meant to be called once, at application startup. Returns the number of
    rows recovered.
    """
    session = get_session()

    try:
        orphaned = session.query(Signal).filter(Signal.status == "PROCESSING").all()
        count = len(orphaned)

        for signal in orphaned:
            signal.status = "OPEN"

        session.commit()
        return count

    except Exception as e:
        session.rollback()
        logger.error("Failed to reap orphaned PROCESSING signals: %s", e)
        return 0

    finally:
        session.close()


def schedule_signal_retry(signal_id) -> bool:
    """On a transient processing failure (see
    core/engine.py::DecisionEngine.process_signal()'s except block),
    increment the signal's retry_count and either schedule a
    backoff-delayed retry (status -> OPEN, next_retry_at set per
    config.SIGNAL_RETRY_BACKOFF_SECONDS) or, once
    config.MAX_SIGNAL_RETRIES is exhausted, leave the signal untouched for
    the caller to mark REJECTED instead.

    Deliberately does NOT apply to the deliberate REJECTED verdicts from
    the decision pipeline or risk manager (execution/execution_loop.py) --
    those are real business decisions, not transient failures, and never
    call this function.

    Returns True if a retry was scheduled, False if retries are already
    exhausted (or the signal/session lookup failed) -- the caller should
    fall back to update_signal_status(signal_id, "REJECTED") on False.
    """
    if signal_id is None:
        logger.warning("schedule_signal_retry called with None signal_id")
        return False

    session = get_session()

    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            logger.warning("Signal %s not found for retry scheduling", signal_id)
            return False

        if signal.retry_count >= MAX_SIGNAL_RETRIES:
            return False

        signal.retry_count += 1
        delay_index = min(signal.retry_count - 1, len(SIGNAL_RETRY_BACKOFF_SECONDS) - 1)
        delay_seconds = SIGNAL_RETRY_BACKOFF_SECONDS[delay_index]
        signal.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)
        signal.status = "OPEN"
        session.commit()
        logger.info(
            "Signal %s scheduled for retry %d/%d in %ds",
            signal_id, signal.retry_count, MAX_SIGNAL_RETRIES, delay_seconds,
        )
        return True

    except Exception as e:
        session.rollback()
        logger.error("Failed to schedule retry for signal %s: %s", signal_id, e)
        return False

    finally:
        session.close()
