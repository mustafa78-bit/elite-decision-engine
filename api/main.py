import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, Optional

import sentry_sdk
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.events import (
    CandlePayload,
    CandleUpdateEvent,
    MarketEvent,
    MarketPayload,
    PricePayload,
    PriceUpdateEvent,
    RiskEvent,
    RiskPayload,
    VolumePayload,
    VolumeUpdateEvent,
    serialize,
)
from api.middleware import auth_middleware
from api.rate_limit import limiter
from api.routes.analytics import router as analytics_router
from api.routes.auth import router as auth_router
from api.routes.backtest import router as backtest_router
from api.routes.coordination import router as coordination_router
from api.routes.council import router as council_router
from api.routes.dashboard import router as dashboard_router
from api.routes.evidence import router as evidence_router
from api.routes.execution import router as execution_router
from api.routes.explanation import router as explanation_router
from api.routes.funding import router as funding_router
from api.routes.intelligence import router as intelligence_router
from api.routes.journal import router as journal_router
from api.routes.kpi import router as kpi_router
from api.routes.market import router as market_router
from api.routes.market_live import router as market_live_router
from api.routes.monitoring import router as monitoring_router
from api.routes.notifications import router as notifications_router
from api.routes.ollo import router as ollo_router
from api.routes.open_interest import router as open_interest_router
from api.routes.paper import router as paper_router
from api.routes.paper_trading import router as paper_trading_router
from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.portfolio_detail import router as portfolio_detail_router
from api.routes.preferences import router as preferences_router
from api.routes.regime import router as regime_router
from api.routes.risk import router as risk_router
from api.routes.scanner import router as scanner_router
from api.routes.signals import router as signals_router
from api.routes.signals_ranking import router as signals_ranking_router
from api.routes.simulator import router as simulator_router
from api.routes.temporary_watch import router as temporary_watch_router
from api.routes.terminal import router as terminal_router
from api.routes.timeline import router as timeline_router
from api.routes.trading_control import router as trading_control_router
from api.routes.users import router as users_router
from api.routes.watchlists import router as watchlists_router
from api.routes.whale import router as whale_router
from api.routes.widgets import router as widgets_router
from api.websocket.manager import WebSocketManager
from config import (
    API_ENV,
    AUTO_TRADING_ENABLED,
    CORS_ORIGINS,
    DEBUG,
    HEALTH_CHECK_INTERVAL_SECONDS,
    SCAN_INTERVAL_SECONDS,
    SENTRY_DSN,
)
from core.engine import DecisionEngine
from database import FINAL_STATUSES, Trade, get_session
from execution.execution_loop import ExecutionLoop
from execution.paper import PaperExecutor as PaperDomainExecutor
from execution.paper_executor import PaperExecutor
from execution.trade_engine import TradeEngine
from market.services import MarketDataService
from market_data.btc_health import BTCHealth
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from monitoring.health import HealthService
from notifications.dispatcher import NotificationDispatcher
from scanner.core import OpportunityScanner
from scoring.regime_ai import RegimeAI
from scoring.risk_engine import RiskEngine
from services.signal_generator import generate_signals

logger = logging.getLogger(__name__)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

if API_ENV == "production" and ("*" in origins or not origins):
    # CORSMiddleware below is registered with allow_credentials=True
    # (hardcoded, not conditional). Starlette's CORS handling for
    # allow_origins=["*"] combined with allow_credentials=True reflects
    # back whatever Origin header the browser actually sent (rather than
    # a literal "*"), so any website can make credentialed (cookie/Bearer-
    # token-bearing) cross-origin requests and read the responses. The
    # equivalent check already exists in startup.py's StartupValidator,
    # but the real uvicorn entrypoint (this file) never calls it -- fail
    # here instead of relying on a check that silently never runs.
    raise RuntimeError(
        "FATAL: CORS_ORIGINS must be an explicit, non-wildcard origin list "
        "when API_ENV=production -- combined with allow_credentials=True, "
        "a wildcard origin lets any website make authenticated cross-origin "
        "requests against this API."
    )

# Error tracking only (no performance tracing/session replay/profiling) --
# no-op when SENTRY_DSN is unset, matching every other optional integration
# in config.py (TELEGRAM_TOKEN, HL_API_KEY, etc). Must run before the
# FastAPI(...) instance below is constructed so Sentry's FastAPI/Starlette
# auto-instrumentation actually attaches to it.
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, environment=API_ENV, send_default_pii=False)

_background_tasks: set[asyncio.Task] = set()
_ollo_service: Any | None = None


def _on_task_done(task_name: str) -> Callable[[asyncio.Task], None]:
    """Build a done-callback that logs a critical alert if `task_name`'s
    background task dies from an unhandled exception. Each of the 6 tasks
    started in lifespan() runs forever via its own `while True` loop with
    per-iteration try/except -- this is a safety net for what those loops'
    own except blocks can't catch (a bug in the except handler itself, an
    exception outside the try, or a task like the Telegram bot that may not
    have that wrapper at all). Without this, an unhandled exception in a
    background task silently surfaces only as Python's default "Task
    exception was never retrieved" warning at garbage-collection time.
    """
    def _callback(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.critical(
                "Background task '%s' died unexpectedly: %s", task_name, exc, exc_info=exc,
            )
    return _callback


@asynccontextmanager
async def lifespan(app: FastAPI):
    from logging_config import setup_logging
    setup_logging()
    logger.info("Application starting up")

    # Provision/upgrade the DB schema before anything else touches it. This
    # uvicorn entrypoint previously never ran any schema setup at all --
    # database.create_tables() existed but was only ever wired into the
    # separate app.py/startup.py CLI path, which the real Docker image
    # (`CMD uvicorn api.main:app`) never runs. The live schema has only ever
    # existed because create_tables() was run manually at some point in the
    # past; this closes that gap going forward.
    import database
    database.run_migrations()

    # Recover Signal rows orphaned in PROCESSING status by a prior process
    # crash (see database.reap_orphaned_processing_signals docstring). Runs
    # unconditionally -- the orphaned rows exist independent of whether
    # AUTO_TRADING_ENABLED is on, and must run before the scan/decision-engine
    # loops below start touching signals.
    recovered = database.reap_orphaned_processing_signals()
    if recovered > 0:
        logger.info("Recovered %d orphaned PROCESSING signal(s) on startup", recovered)

    # Initialize OLLO Service
    global _ollo_service
    try:
        from services.ai.provider_factory import create_ai_service
        from services.ollo.ollo_service import OLLOService
        _ai_svc = create_ai_service()
        _ollo_service = OLLOService(_ai_svc)
        logger.info("OLLO Service initialized successfully")
    except Exception as e:
        logger.warning("OLLO Service initialization failed: %s", e)

    # Start Telegram bots if configured -- "trades" (status/brief/ask
    # commands + trade/health alerts) plus the 2 push-only news/VC bots.
    # New-listing alerts (services/listings_service.py) route through the
    # "vc_funding" bot already started here, not a separate bot instance.
    from services.telegram.bot import TelegramBotManager
    running_loop = asyncio.get_running_loop()
    started_bot_managers = []
    for bot_name in ("trades", "news", "vc_funding"):
        bot_manager = TelegramBotManager.get_instance(bot_name)
        bot_manager.set_event_loop(running_loop)
        if bot_manager.setup():
            bot_task = asyncio.create_task(bot_manager.start())
            bot_task.add_done_callback(_on_task_done(f"Telegram bot '{bot_name}'"))
            _background_tasks.add(bot_task)
            started_bot_managers.append(bot_manager)

    # Single dispatcher shared by every real trade/health event source so
    # TRADE_OPENED/TRADE_CLOSED actually reach the real WebSocketManager --
    # TradeEngine/PaperExecutor previously default-constructed their own
    # private NotificationDispatcher(websocket_manager=None) when not given
    # one explicitly, so trade events were persisted to DB and sent to
    # Telegram but never broadcast over any websocket in production.
    shared_dispatcher = NotificationDispatcher(websocket_manager=manager)

    if AUTO_TRADING_ENABLED:
        scan_task = asyncio.create_task(_scan_and_generate_signals())
        scan_task.add_done_callback(_on_task_done("Scan-and-signal task"))
        _background_tasks.add(scan_task)

        decision_engine = DecisionEngine(
            execution_loop=ExecutionLoop(
                trade_engine=TradeEngine(notifications=shared_dispatcher),
                paper_executor=PaperExecutor(notifications=shared_dispatcher),
                trade_journal=PaperDomainExecutor(),
            )
        )
        engine_task = asyncio.create_task(decision_engine.run())
        engine_task.add_done_callback(_on_task_done("Decision engine"))
        _background_tasks.add(engine_task)

        logger.info(
            "AUTO_TRADING_ENABLED=true: scan-and-signal and decision-engine "
            "background tasks started"
        )

    task = asyncio.create_task(_periodic_broadcast())
    task.add_done_callback(_on_task_done("Periodic broadcast"))
    _background_tasks.add(task)

    health_task = asyncio.create_task(_health_monitor_loop(shared_dispatcher))
    health_task.add_done_callback(_on_task_done("Health monitor loop"))
    _background_tasks.add(health_task)

    news_task = asyncio.create_task(_news_alert_loop())
    news_task.add_done_callback(_on_task_done("News alert loop"))
    _background_tasks.add(news_task)

    listings_task = asyncio.create_task(_listings_alert_loop())
    listings_task.add_done_callback(_on_task_done("Listings alert loop"))
    _background_tasks.add(listings_task)

    yield

    logger.info("Application shutting down")
    for bot_manager in started_bot_managers:
        try:
            await bot_manager.stop()
        except Exception as e:
            logger.warning("Telegram Bot '%s' shutdown error: %s", bot_manager.name, e)

    task.cancel()
    for t in _background_tasks:
        if not t.done():
            t.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    try:
        from startup import shutdown
        shutdown()
    except Exception as e:
        logger.warning("Shutdown handler error: %s", e)


app = FastAPI(
    title="Elite Decision Engine",
    debug=DEBUG,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", "N/A")
    logger.exception("[%s] Unhandled exception on %s %s", rid, request.method, request.url.path)
    # Sentry's FastAPI/Starlette auto-instrumentation only sees exceptions
    # that propagate unhandled through the ASGI stack -- registering this
    # handler for the base Exception class means every unhandled exception
    # is caught and converted to a normal 500 response right here, so it
    # never reaches Sentry automatically. Explicit capture (a safe no-op
    # when SENTRY_DSN is unset / sentry_sdk.init() was never called).
    sentry_sdk.capture_exception(exc)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": rid},
    )
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    rid = getattr(request.state, "request_id", "N/A")
    logger.warning(
        "[%s] Validation error on %s %s: %s", rid, request.method, request.url.path, exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": exc.errors(), "body": exc.body, "request_id": rid}
        ),
    )


app.middleware("http")(auth_middleware)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if API_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Registered LAST so it ends up OUTERMOST (Starlette's add_middleware prepends,
# then build_middleware_stack wraps in reverse) -- CORS must see and respond to
# preflight OPTIONS requests before auth_middleware gets a chance to reject them
# with a header-less 401, which the browser would then treat as a failed
# preflight and block the real request. See docs/FRONTEND_AUTH_FIX_REPORT.md.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(auth_router)
app.include_router(backtest_router)
app.include_router(execution_router)
app.include_router(intelligence_router)
app.include_router(funding_router)
app.include_router(journal_router)
app.include_router(market_router)
app.include_router(market_live_router)
app.include_router(open_interest_router)
app.include_router(monitoring_router)
app.include_router(notifications_router)
app.include_router(paper_router)
app.include_router(paper_trading_router)
app.include_router(performance_router)
app.include_router(portfolio_router)
app.include_router(regime_router)
app.include_router(risk_router)
app.include_router(signals_router)
app.include_router(signals_ranking_router)
app.include_router(trading_control_router)
app.include_router(users_router)
app.include_router(explanation_router)
app.include_router(analytics_router)
app.include_router(kpi_router)
app.include_router(coordination_router)
app.include_router(dashboard_router)
app.include_router(widgets_router)
app.include_router(preferences_router)
app.include_router(watchlists_router)
app.include_router(temporary_watch_router)
app.include_router(timeline_router)
app.include_router(scanner_router)
app.include_router(terminal_router)
app.include_router(portfolio_detail_router)
app.include_router(evidence_router)
app.include_router(simulator_router)
app.include_router(ollo_router)
app.include_router(council_router)
app.include_router(whale_router)

manager = WebSocketManager()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "elite-decision-engine",
        "env": API_ENV,
        "uptime_seconds": round(HealthService.uptime(), 2),
    }


@app.websocket("/ws/trades")
async def ws_trades(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="trades")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/analytics")
async def ws_analytics(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="analytics")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="dashboard")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/portfolio")
async def ws_portfolio(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="portfolio")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="notifications")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/scanner")
async def ws_scanner(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="scanner")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/preferences")
async def ws_preferences(websocket: WebSocket) -> None:
    await manager.connect(websocket, room="preferences")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


_evidence_engine: Optional = None

try:
    from decision.evidence import EvidenceEngine
    _evidence_engine = EvidenceEngine()
    logger.info("Evidence engine initialized")
except Exception as e:
    _evidence_engine = None
    logger.warning("Evidence engine initialization failed: %s", e)

_mip_service: MarketDataService | None = None


def get_mip() -> MarketDataService:
    global _mip_service
    if _mip_service is None:
        _mip_service = MarketDataService()
    return _mip_service


async def _broadcast_market() -> None:
    try:
        asset = get_mip().get_asset("BTC")
        if asset.is_empty:
            return

        price = asset.price
        df = asset.ohlcv
        btc_ctx = asset.context.get("btc", {})
        btc_trend = btc_ctx.get("btc_trend", "NEUTRAL")
        btc_score = 1.0 if btc_trend == "BULLISH" else (0.0 if btc_trend == "BEARISH" else 0.5)
        vol_val = asset.indicators.get("volatility", 0)

        from scoring.regime_ai import RegimeAI
        regime = RegimeAI()
        reg = regime.detect({
            "ema20": asset.indicators.get("ema20", 0),
            "ema50": asset.indicators.get("ema50", 0),
            "ema200": asset.indicators.get("ema200", 0),
            "atr": asset.indicators.get("atr", 0),
            "close": price,
            "rsi": asset.indicators.get("rsi", 50),
        })

        event = MarketEvent(payload=MarketPayload(
            price=price,
            regime=reg.get("regime", "UNKNOWN"),
            btc_health_score=btc_score,
            volatility=vol_val,
        ))
        await manager.broadcast(serialize(event))

        price_event = PriceUpdateEvent(payload=PricePayload(
            symbol="BTC",
            price=price,
            volume=float(df["volume"].iloc[-1]),
        ))
        await manager.broadcast(serialize(price_event))

        latest = df.iloc[-1]
        candle_event = CandleUpdateEvent(payload=CandlePayload(
            symbol="BTC",
            open=float(latest["open"]),
            high=float(latest["high"]),
            low=float(latest["low"]),
            close=float(latest["close"]),
            volume=float(latest["volume"]),
            timestamp=int(latest["timestamp"]) if "timestamp" in latest else 0,
        ))
        await manager.broadcast(serialize(candle_event))

        volume_24h = float(df["volume"].tail(24).sum()) if len(df) >= 24 else float(df["volume"].sum())
        vol_event = VolumeUpdateEvent(payload=VolumePayload(
            symbol="BTC",
            volume_24h=volume_24h,
        ))
        await manager.broadcast(serialize(vol_event))
    except Exception:
        logger.exception("Market broadcast failed")


async def _broadcast_risk() -> None:
    try:
        session = get_session()
        try:
            all_trades = session.query(Trade).all()
        finally:
            session.close()

        risk_engine = RiskEngine()
        risk_score = risk_engine.score({"atr": 0}, {"score": 0})

        # Per-user open_trades count -- the old version summed every
        # tenant's open trades into one number broadcast to every
        # connected client, leaking an aggregate cross-user signal. Group
        # by owner (None = orphaned/pre-migration rows, falls back to
        # everyone via broadcast_to_owner, same NULL-fallback convention
        # as services/notification_service.py's _owned_by()) and send each
        # owner only their own count. Union with connected_user_ids() so a
        # user with zero trades still gets a real (open_trades=0) update
        # instead of none at all.
        trades_by_owner: dict[int | None, list] = {}
        for t in all_trades:
            trades_by_owner.setdefault(t.user_id, []).append(t)

        owner_ids = set(trades_by_owner.keys()) | manager.connected_user_ids()
        for owner_user_id in owner_ids:
            open_trades = [t for t in trades_by_owner.get(owner_user_id, []) if t.status == "OPEN"]
            event = RiskEvent(payload=RiskPayload(
                risk_score=risk_score,
                open_trades=len(open_trades),
                max_open_trades=3,
                daily_loss=0.0,
                max_daily_loss=10000,
            ))
            await manager.broadcast_to_owner(serialize(event), owner_user_id)
    except Exception:
        logger.exception("Risk broadcast failed")


async def _scan_and_generate_signals() -> None:
    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

            def _run_scan():
                return OpportunityScanner().scan()

            opportunities = await asyncio.to_thread(_run_scan)
            created = await asyncio.to_thread(generate_signals, opportunities)
            logger.info(
                "Auto-trading scan: %d new signal(s) created from %d opportunity(ies)",
                created, len(opportunities),
            )
        except asyncio.CancelledError:
            logger.info("Scan-and-signal task cancelled")
            raise
        except Exception:
            logger.exception("Scan-and-signal task iteration failed")


async def _periodic_broadcast() -> None:
    while True:
        try:
            await asyncio.sleep(30)
            await _broadcast_market()
            await _broadcast_risk()
        except asyncio.CancelledError:
            logger.info("Periodic broadcast cancelled")
            raise
        except Exception:
            logger.exception("Periodic broadcast iteration failed")


async def _health_monitor_loop(dispatcher: NotificationDispatcher) -> None:
    """Periodically check core system health and alert (Telegram + websocket)
    only when a component transitions between healthy and unhealthy.

    Runs unconditionally (not gated behind AUTO_TRADING_ENABLED) — system health
    matters regardless of whether auto-trading is on.
    """
    while True:
        try:
            await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
            await asyncio.to_thread(HealthService.check_and_alert, dispatcher)
        except asyncio.CancelledError:
            logger.info("Health monitor loop cancelled")
            raise
        except Exception:
            logger.exception("Health monitor loop iteration failed")


async def _news_alert_loop() -> None:
    """Periodically push proactive Telegram alerts for market-moving crypto
    news and institutional/VC project-funding news. See
    SPRINT_JULES_TELEGRAM_NEWS_ALERTS.md for the full design rationale.
    """
    from services.news_job_service import NEWS_JOB_INTERVAL_SECONDS, run_news_alert_cycle

    while True:
        try:
            await asyncio.sleep(NEWS_JOB_INTERVAL_SECONDS)
            await asyncio.to_thread(run_news_alert_cycle)
        except asyncio.CancelledError:
            logger.info("News alert loop cancelled")
            raise
        except Exception:
            logger.exception("News alert loop iteration failed")


async def _listings_alert_loop() -> None:
    """Periodically push proactive Telegram alerts for new Binance spot
    listings. See services/listings_service.py for the full design
    rationale (Binance only for now, not OKX/Bybit).
    """
    from services.listings_service import LISTINGS_JOB_INTERVAL_SECONDS, run_listings_alert_cycle

    while True:
        try:
            await asyncio.sleep(LISTINGS_JOB_INTERVAL_SECONDS)
            await asyncio.to_thread(run_listings_alert_cycle)
        except asyncio.CancelledError:
            logger.info("Listings alert loop cancelled")
            raise
        except Exception:
            logger.exception("Listings alert loop iteration failed")



