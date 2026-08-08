import pytest
from sqlalchemy.exc import IntegrityError

from database import Signal, Trade


def test_trade_signal_id_foreign_key_constraint(db_session):
    # 1. Nullable check: creating a trade with signal_id=None should succeed
    trade_null = Trade(
        signal_id=None,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49000.0,
        tp1=52000.0,
    )
    db_session.add(trade_null)
    db_session.flush()
    assert trade_null.id is not None

    # 2. Invalid FK check: creating a trade with signal_id=99999 (non-existent signal) should raise IntegrityError
    trade_invalid = Trade(
        signal_id=99999,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49000.0,
        tp1=52000.0,
    )
    db_session.add(trade_invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()

    # Roll back after the failed flush/transaction error
    db_session.rollback()

    # 3. Valid FK check: creating a trade with a real signal_id should succeed
    sig = Signal(
        id=12345,
        symbol="BTCUSDT",
        side="LONG",
    )
    db_session.add(sig)
    db_session.flush()

    trade_valid = Trade(
        signal_id=12345,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49000.0,
        tp1=52000.0,
    )
    db_session.add(trade_valid)
    db_session.flush()
    assert trade_valid.id is not None
