from fastapi import APIRouter
from research_agent.app.config.config import settings

router = APIRouter()

@router.get("", response_model=dict)
async def health_check():
    """
    Performs a standard diagnostic check of the service status.
    Returns general app info, runtime environment, and debug status.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG
    }
