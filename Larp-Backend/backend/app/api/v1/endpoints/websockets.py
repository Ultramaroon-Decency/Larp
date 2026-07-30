"""WebSocket endpoints streaming real-time research updates to frontend clients."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.core.websocket import manager
from app.redis import get_redis

logger = get_logger("websocket_endpoint")
router = APIRouter()


@router.websocket("/research/{job_id}")
async def research_websocket_endpoint(
    websocket: WebSocket,
    job_id: UUID,
    token: str | None = Query(default=None, description="Optional JWT access token"),
):
    """WebSocket endpoint streaming live research execution updates to frontend clients.

    Frontend Usage:
    const ws = new WebSocket("ws://localhost:8000/api/v1/ws/research/JOB_UUID?token=JWT_TOKEN");
    ws.onmessage = (event) => { const data = JSON.parse(event.data); console.log(data); };
    """
    # ── 1. Authenticate Token (if provided) ────────────────────────────
    user_id_str: str | None = None
    if token:
        try:
            payload = decode_access_token(token)
            user_id_str = payload.sub
        except Exception as exc:
            logger.warning("WebSocket auth failed", error=str(exc), job_id=str(job_id))
            await websocket.close(code=4001, reason="Invalid or expired access token")
            return

    # ── 2. Accept WebSocket Connection ─────────────────────────────────
    await manager.connect(websocket, job_id)

    # ── 3. Send Connection Confirmation Payload ────────────────────────
    await manager.send_personal_message(
        {
            "event": "connected",
            "job_id": str(job_id),
            "status": "listening",
            "user_id": user_id_str,
            "message": "Subscribed to live research job updates",
        },
        websocket,
    )

    # ── 4. Redis PubSub Subscriber Listener Task ───────────────────────
    redis_client: Redis = await get_redis()
    pubsub = redis_client.pubsub()
    channel_name = f"research:{job_id}"

    async def listen_redis_pubsub():
        """Listen to Redis channel 'research:{job_id}' and stream updates to this client."""
        try:
            await pubsub.subscribe(channel_name)
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    try:
                        event_payload = json.loads(raw_data)
                        await websocket.send_json(event_payload)
                    except Exception:
                        await websocket.send_text(raw_data)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("Redis PubSub listener error", error=str(exc))
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
            except Exception:
                pass

    pubsub_task = asyncio.create_task(listen_redis_pubsub())

    # ── 5. Main WebSocket Event Loop ───────────────────────────────────
    try:
        while True:
            # Keep-alive receive loop (listens for client ping/messages)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client", job_id=str(job_id))
    except Exception as exc:
        logger.warning("WebSocket connection exception", error=str(exc), job_id=str(job_id))
    finally:
        pubsub_task.cancel()
        manager.disconnect(websocket, job_id)
