"""Shared fixtures for the Elite Decision Engine test suite.

Usage:
    def test_foo(db_session):
        # db_session is a SQLAlchemy session connected to the test database.
        # All changes are rolled back automatically after each test.
        # Production database is never touched.

    def test_api(api_client):
        # api_client is a FastAPI TestClient with ``database.get_session``
        # patched to use the test database.  Routes that only read/write the
        # database (no external APIs) work out of the box.
"""

import os

os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("API_ENV", "test")
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from logging_config import setup_logging

setup_logging()


TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


def _default_engine():
    """Return a shared in-memory SQLite engine used by all tests.

    ``StaticPool`` ensures every call to ``engine.connect()`` returns the
    **same** connection, so all fixtures and route handlers operate on a
    single shared in-memory database whose outer transaction is rolled back
    between tests.
    """
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


@pytest.fixture(scope="session")
def test_engine():
    """SQLAlchemy engine connected to the test database.

    All tables are created once per test session and dropped at the end.
    """
    if TEST_DATABASE_URL == "sqlite:///:memory:":
        engine = _default_engine()
    else:
        engine = create_engine(TEST_DATABASE_URL, echo=False)

    if "sqlite" in repr(engine.url):
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

    A raw ``BEGIN`` is issued via ``exec_driver_sql`` immediately after
    ``begin()`` to force a **real** SQLite ``BEGIN``.  Without this,
    SQLAlchemy's *autobegin* defers the ``BEGIN`` until the first DML
    statement; when that first DML is a ``SAVEPOINT`` (created by
    ``session.begin(nested=True)``), SQLite auto-starts a transaction
    that is **permanently** committed by ``RELEASE SAVEPOINT``, making
    the subsequent ``ROLLBACK`` a no-op.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    connection.exec_driver_sql("BEGIN")
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture
def session_factory(db_connection):
    """Return a callable that creates a new session on the test connection.

    Each session starts a nested transaction (savepoint) inside the
    outer transaction managed by ``db_connection``.  When production
    code calls ``commit()`` the savepoint is released, making changes
    visible to other sessions on the same connection.  The outer
    transaction rollback at teardown undoes everything.
    """
    maker = sessionmaker(bind=db_connection)

    def _make():
        session = maker()
        session.begin(nested=True)
        return session

    return _make


@pytest.fixture
def db_session(session_factory, monkeypatch):
    """Provide a test session with all ``get_session`` call sites patched.

    Recursively patches all module-level instances of ``get_session`` with local
    SQLite transactional sessions, completely isolating test transactions from
    host-level database adapters.
    """
    import sys
    monkeypatch.setattr("database.get_session", session_factory)

    for mod_name in list(sys.modules.keys()):
        mod = sys.modules[mod_name]
        if hasattr(mod, "get_session") and mod_name != "database":
            mod.get_session = session_factory

    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def api_client(session_factory, monkeypatch):
    """Provide a FastAPI TestClient with every ``get_session`` call site patched.

    Steps:
    1. Monkeypatch ``database.get_session`` (covers future imports).
    2. Walk ``sys.modules`` and **directly** override ``.get_session`` on every
       module that already imported it (bypasses ``monkeypatch`` restore so
       stale references don't leak between tests).
    3. Import ``api.main`` (uses the patched ``database.get_session`` and also
       the already-patched module-level references for route modules that are
       cached from previous tests).

    Usage::

        def test_list_signals(api_client):
            resp = api_client.get("/signals")
            assert resp.status_code == 200
    """
    import sys

    monkeypatch.setattr("database.get_session", session_factory)

    for mod_name in list(sys.modules.keys()):
        mod = sys.modules[mod_name]
        if hasattr(mod, "get_session") and mod_name != "database":
            mod.get_session = session_factory

    from api.main import app
    from auth.jwt import create_access_token

    token = create_access_token({"sub": "1", "username": "test"})
    client = TestClient(app)
    client.headers.setdefault("Authorization", f"Bearer {token}")
    yield client
    client.close()
