import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from api.routes.performance import router as performance_router
from api.websocket.manager import WebSocketManager


logger = logging.getLogger(__name__)

app = FastAPI(title="Elite Decision Engine")
app.include_router(performance_router)

manager = WebSocketManager()


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
