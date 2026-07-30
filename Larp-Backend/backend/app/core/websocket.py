"""WebSocket ConnectionManager and real-time PubSub broadcasting module for live research updates."""

import json
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger("websocket")


class ConnectionManager:
    """Manages active WebSocket connections grouped by research job ID."""

    def __init__(self) -> None:
        # Maps job_id -> List[WebSocket]
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: UUID) -> None:
        """Accept a WebSocket connection and assign it to a research job_id group."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

        logger.info(
            "WebSocket client connected",
            job_id=str(job_id),
            total_job_clients=len(self.active_connections[job_id]),
        )

    def disconnect(self, websocket: WebSocket, job_id: UUID) -> None:
        """Remove a WebSocket client connection on disconnect."""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        logger.info(
            "WebSocket client disconnected",
            job_id=str(job_id),
        )

    async def send_personal_message(
        self, message: dict, websocket: WebSocket
    ) -> None:
        """Send a JSON payload directly to a specific connected WebSocket client."""
        try:
            await websocket.send_json(message)
        except Exception as exc:
            logger.warning("Error sending personal WebSocket message", error=str(exc))

    async def broadcast_to_job(self, job_id: UUID, message: dict) -> None:
        """Broadcast a live progress event payload to all clients subscribed to job_id."""
        if job_id not in self.active_connections:
            return

        disconnected_sockets: List[WebSocket] = []
        for socket in self.active_connections[job_id]:
            try:
                await socket.send_json(message)
            except Exception:
                disconnected_sockets.append(socket)

        # Cleanup failed sockets
        for socket in disconnected_sockets:
            self.disconnect(socket, job_id)

        logger.info(
            "Broadcasted live update to job subscribers",
            job_id=str(job_id),
            active_clients=len(self.active_connections.get(job_id, [])),
        )


# Singleton ConnectionManager instance
manager = ConnectionManager()
