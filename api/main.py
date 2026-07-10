import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from monitoring.health import HealthService
from api.routes.auth import router as auth_router
from api.routes.backtest import router as backtest_router
from api.routes.execution import router as execution_router
from api.routes.intelligence import router as intelligence_router
from api.routes.journal import router as journal_router
from api.routes.market import router as market_router
from api.routes.market_live import router as market_live_router
from api.routes.monitoring import router as monitoring_router
from api.routes.notifications import router as notifications_router
from api.routes.paper_trading import router as paper_trading_router
from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.regime import router as regime_router
from api.routes.risk import router as risk_router
from api.routes.signals import router as signals_router
from api.routes.signals_ranking import router as signals_ranking_router
from api.routes.trading_control import router as trading_control_router
from api.routes.users import router as users_router
from api.routes.explanation import router as explanation_router
from api.routes.analytics import router as analytics_router
from api.routes.kpi import router as kpi_router
from api.routes.coordination import router as coordination_router
from api.routes.dashboard import router as dashboard_router
from api.routes.widgets import router as widgets_router
from api.routes.preferences import router as preferences_router
from api.routes.watchlists import router as watchlists_router
from api.routes.timeline import router as timeline_router
from api.routes.scanner import router as scanner_router
from api.routes.portfolio_detail import router as portfolio_detail_router
from api.websocket.manager import WebSocketManager
from config import API_ENV, CORS_ORIGINS, DEBUG
from database import FINAL_STATUSES, Trade, get_session
from market_data.btc_health import BTCHealth
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from market.services import MarketDataService
from scoring.regime_ai import RegimeAI
from scoring.risk_engine import RiskEngine


logger = logging.getLogger(__name__)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

_background_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    task = asyncio.create_task(_periodic_broadcast())
    _background_tasks.add(task)
    yield
    logger.info("Application shutting down")
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", "N/A")
    logger.exception("[%s] Unhandled exception on %s %s", rid, request.method, request.url.path)
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
        content={"detail": exc.errors(), "body": exc.body, "request_id": rid},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(auth_middleware)

app.include_router(auth_router)
app.include_router(backtest_router)
app.include_router(execution_router)
app.include_router(intelligence_router)
app.include_router(journal_router)
app.include_router(market_router)
app.include_router(market_live_router)
app.include_router(monitoring_router)
app.include_router(notifications_router)
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
app.include_router(timeline_router)
app.include_router(scanner_router)
app.include_router(portfolio_detail_router)

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


_mip_service: Optional[MarketDataService] = None


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

        open_trades = [t for t in all_trades if t.status == "OPEN"]
        closed_count = len([t for t in all_trades if t.status in FINAL_STATUSES])

        risk_engine = RiskEngine()
        risk_score = risk_engine.score({"atr": 0}, {"score": 0})

        event = RiskEvent(payload=RiskPayload(
            risk_score=risk_score,
            open_trades=len(open_trades),
            max_open_trades=3,
            daily_loss=0.0,
            max_daily_loss=10000,
        ))
        await manager.broadcast(serialize(event))
    except Exception:
        logger.exception("Risk broadcast failed")


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



