import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
from api.routes.auth import router as auth_router
from api.routes.execution import router as execution_router
from api.routes.intelligence import router as intelligence_router
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
from api.routes.users import router as users_router
from api.websocket.manager import WebSocketManager
from config import API_ENV, CORS_ORIGINS, DEBUG
from database import Trade, get_session
from market_data.btc_health import BTCHealth
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from scoring.regime_engine import RegimeEngine
from scoring.risk_engine import RiskEngine


logger = logging.getLogger(__name__)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})

app = FastAPI(
    title="Elite Decision Engine",
    debug=DEBUG,
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
app.include_router(execution_router)
app.include_router(intelligence_router)
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
app.include_router(users_router)

manager = WebSocketManager()


@app.get("/health")
def health():
    return {"status": "ok", "service": "elite-decision-engine", "env": API_ENV}


@app.websocket("/ws/trades")
async def ws_trades(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


async def _broadcast_market() -> None:
    try:
        collector = HyperliquidCollector()
        indicators = IndicatorEngine()
        btc = BTCHealth()
        vol = VolatilityEngine()
        regime = RegimeEngine()

        df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        if df.empty:
            return

        values = indicators.calculate(df)
        btc_score = btc.score()
        vol_score = vol.score(values)
        reg = regime.detect(values)
        price = float(df["close"].iloc[-1])

        event = MarketEvent(payload=MarketPayload(
            price=price,
            regime=reg["regime"],
            btc_health_score=btc_score,
            volatility=vol_score["volatility"],
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
        await asyncio.sleep(30)
        await _broadcast_market()
        await _broadcast_risk()


@app.on_event("startup")
async def start_broadcaster() -> None:
    asyncio.create_task(_periodic_broadcast())
