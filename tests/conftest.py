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


@pytest.fixture(autouse=True)
def mock_fundamental_veto(request, monkeypatch):
    """execution/pipeline.py's DecisionPipeline now calls
    council/fundamental_gate.py's check_fundamental_veto() by default for
    every approved signal (FUNDAMENTAL_VETO_ENABLED defaults true -- it's a
    pure safety net, see config.py's comment). That function hits real
    market/news/whale data through MarketDataService -- without this,
    every existing pipeline test that never anticipated it would make
    unmocked real network calls, same class of problem
    mock_global_coin_universe below already guards against. Defaults to
    "never veto" so existing pipeline tests keep their prior behavior;
    tests/test_fundamental_gate.py and the dedicated pipeline-integration
    tests override this explicitly to exercise the real veto logic."""
    if "test_fundamental_gate" in request.node.nodeid or "test_pipeline_fundamental_veto" in request.node.nodeid:
        return
    from council.fundamental_gate import FundamentalVetoResult
    monkeypatch.setattr(
        "council.fundamental_gate.check_fundamental_veto",
        lambda *args, **kwargs: FundamentalVetoResult(False, None),
    )


@pytest.fixture(autouse=True)
def _reset_intelligence_service_cache():
    """market.intelligence.service.IntelligenceService.enrich() caches its
    result per-symbol at the class level (see that class's _CACHE_TTL_SECONDS
    comment). Without resetting between tests, a test using a real/default
    symbol (commonly "BTC") could silently reuse another test's cached
    bundle instead of exercising its own mocks."""
    import market.intelligence.service as intelligence_service
    intelligence_service.IntelligenceService._cache = {}
    yield
    intelligence_service.IntelligenceService._cache = {}


@pytest.fixture(autouse=True)
def _reset_news_sentiment_cache():
    """market.intelligence.news.NewsService.classify_sentiment() caches its
    result per exact headline set at the class level (see that class's
    _sentiment_cache comment). Without resetting between tests, a test using
    a common headline fixture could silently reuse another test's cached
    (possibly mocked) sentiment instead of exercising its own mocks."""
    import market.intelligence.news as news_service
    news_service.NewsService._sentiment_cache = {}
    yield
    news_service.NewsService._sentiment_cache = {}


@pytest.fixture(autouse=True)
def _reset_shared_ai_provider():
    """services.ai.provider_factory.get_shared_provider() memoizes one
    AIProvider at module level for the whole process, by design (see its
    docstring -- that's what makes rate limiting actually coordinate across
    OLLO/council/news/Telegram). Without resetting it between tests, the
    first test to call it would leak its (possibly mocked) provider into
    every later test that expects create_provider()'s current mock/env vars
    to take effect."""
    import services.ai.provider_factory as provider_factory
    provider_factory._shared_provider = None
    yield
    provider_factory._shared_provider = None


@pytest.fixture(autouse=True)
def _reset_shared_multi_provider():
    """market.provider.multi.get_shared_multi_provider() memoizes one
    MultiProvider at module level for the whole process, by design (see its
    docstring -- 19 real call sites used to each build their own instance
    with an uncoordinated rate limiter, which is exactly the bug this
    singleton exists to fix). Without resetting it between tests, the first
    test to call it would leak its (possibly mocked) instance into every
    later test that expects its own injected `collector=`/`provider=` to
    take effect via the `or get_shared_multi_provider()` default."""
    import market.provider.multi as multi_module
    multi_module._shared_instance = None
    yield
    multi_module._shared_instance = None


@pytest.fixture(autouse=True)
def mock_global_coin_universe(request, monkeypatch):
    """Globally mock the dynamic coin universe Binance network calls to prevent unmocked requests."""
    if "test_universe" in request.node.nodeid:
        return

    import sys
    mock_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    # 1. Monkeypatch market_data.universe helper and provider functions
    try:
        import market_data.universe as universe
        monkeypatch.setattr(universe, "get_top_volume_symbols", lambda n=None: mock_symbols[:n] if n is not None else mock_symbols)
        if hasattr(universe, "_provider"):
            monkeypatch.setattr(universe._provider, "get_top_volume_symbols", lambda n=None: mock_symbols[:n] if n is not None else mock_symbols)
    except ImportError:
        pass

    # 2. Walk sys.modules to patch any direct imports of get_top_volume_symbols
    for mod_name, mod in list(sys.modules.items()):
        if mod and hasattr(mod, "get_top_volume_symbols") and mod_name != "market_data.universe":
            monkeypatch.setattr(mod, "get_top_volume_symbols", lambda n=None: mock_symbols[:n] if n is not None else mock_symbols)

    # 3. OpportunityScanner()'s default constructor (no explicit symbols=)
    # now queries TemporaryWatchService instead of calling
    # get_top_volume_symbols() -- same "no unmocked I/O by default" concern
    # as above, just a DB read instead of an HTTP call. Tests that construct
    # a scanner without going through the db_session/session_factory
    # fixtures would otherwise hit a real database connection with no test
    # schema. tests/test_temporary_watch_* inject their own real or mock
    # TemporaryWatchService explicitly, which takes precedence over this
    # class-level default regardless.
    if "test_temporary_watch" not in request.node.nodeid:
        from services.temporary_watch_service import TemporaryWatchService
        monkeypatch.setattr(TemporaryWatchService, "active_symbols", lambda self: [])


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
