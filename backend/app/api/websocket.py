"""
SIGMA_ASR_VTT - WebSocket Progress & Metrics Broadcaster
Developer: أصيل السويدي
"""

from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.core.models import JobProgress
from app.infrastructure.logger import logger

router = APIRouter()

class ConnectionManager:
    """Manages active WebSocket connections for live progress streaming."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, token: str) -> bool:
        """Authenticates token and accepts WebSocket connection."""
        if token != settings.SESSION_TOKEN:
            logger.warning(f"Rejected WebSocket connection attempt with invalid token: {token[:4]}...")
            await websocket.close(code=4001, reason="Unauthorized session token")
            return False

        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, payload: dict) -> None:
        """Broadcasts arbitrary payload to all connected frontend clients."""
        if not self.active_connections:
            return

        dead_sockets = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                dead_sockets.add(connection)

        for dead in dead_sockets:
            self.disconnect(dead)

    async def broadcast_progress(self, progress: JobProgress) -> None:
        """Broadcasts job progress update to all connected frontend clients."""
        await self.broadcast(progress.model_dump())

ws_manager = ConnectionManager()

@router.websocket("/ws/progress/{token}")
async def websocket_progress_endpoint(websocket: WebSocket, token: str):
    accepted = await ws_manager.connect(websocket, token)
    if not accepted:
        return

    try:
        while True:
            # Keep connection alive and listen for client heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)
