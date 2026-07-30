"""API v1 router module including REST endpoints, report exports, and WebSocket channels."""

from fastapi import APIRouter
from app.api.v1.endpoints import agents, auth, health, reports, research, users, websockets

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(research.router, prefix="/research", tags=["Research Sessions"])
api_router.include_router(reports.router, prefix="/reports", tags=["Research Reports"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agent Tasks"])
api_router.include_router(websockets.router, prefix="/ws", tags=["WebSockets"])
