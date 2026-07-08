import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.routes.performance import router as performance_router
from api.routes.portfolio import router as portfolio_router
from api.routes.risk import router as risk_router
from api.routes.market import router as market_router
from api.routes.signals import router as signals_router
from api.websocket.manager import WebSocketManager
from config import API_ENV, CORS_ORIGINS, DEBUG


logger = logging.getLogger(__name__)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

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

app.include_router(performance_router)
app.include_router(portfolio_router)
app.include_router(risk_router)
app.include_router(market_router)
app.include_router(signals_router)

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
