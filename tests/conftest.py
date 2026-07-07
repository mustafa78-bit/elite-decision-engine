"""Shared fixtures for the Elite Decision Engine test suite.

Usage:
    def test_foo(db_session):
        # db_session is a SQLAlchemy session connected to the test database.
        # All changes are rolled back automatically after each test.
        # Production database is never touched.
"""

import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base
from logging_config import setup_logging

setup_logging()


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///test_elite.db")


@pytest.fixture(scope="session")
def test_engine():
    """SQLAlchemy engine connected to the test database.

    All tables are created once per test session and dropped at the end.
    """
    engine = create_engine(TEST_DATABASE_URL, echo=False)

    if "sqlite" in TEST_DATABASE_URL:
        _enable_sqlite_pragmas(engine)

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


def _enable_sqlite_pragmas(engine):
    """Enable foreign keys for SQLite test databases."""

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture
def db_connection(test_engine):
    """Provide a database connection wrapped in an outer transaction.

    Every session created during the test (via ``db_session``,
    ``session_factory``, or monkeypatched ``get_session``) uses this
    same connection.  At teardown the outer transaction is rolled back,
    undoing **all** changes including those committed to savepoints by
    production code.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture
def session_factory(db_connection):
    """Return a callable that creates a new session on the test connection.

    The session participates in the outer transaction managed by
    ``db_connection``.  When production code calls ``commit()`` the
    data is flushed to the connection's transaction (no actual SQL
    COMMIT) and the outer transaction rollback at teardown undoes
    everything.

    SQLite + SQLAlchemy does not support rolling back savepoint-released
    changes, so we avoid ``begin(nested=True)`` here.
    """
    maker = sessionmaker(bind=db_connection)

    def _make():
        return maker()

    return _make


@pytest.fixture
def db_session(session_factory, monkeypatch):
    """Provide a test session with all ``get_session`` call sites patched.

    Patches:
    - ``database.get_session`` — covers ``update_signal_status``
    - ``execution.trade_engine.get_session`` — covers ``TradeEngine.create_trade``
    - ``core.engine.get_session`` — covers ``DecisionEngine.get_open_signals``

    The session is bound to the outer transaction managed by
    ``db_connection``, so all changes are rolled back automatically.
    """
    monkeypatch.setattr("database.get_session", session_factory)
    monkeypatch.setattr("execution.trade_engine.get_session", session_factory)
    monkeypatch.setattr("core.engine.get_session", session_factory)

    session = session_factory()
    yield session
    session.close()
