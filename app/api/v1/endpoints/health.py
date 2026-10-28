"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=200,
    summary="Liveness Check",
    description="Returns 200 if the service process is alive.",
)
async def health_live() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.MPESA_ENVIRONMENT,
    }


@router.get(
    "/ready",
    status_code=200,
    summary="Readiness Check",
    description="Returns 200 when the service is ready to serve traffic (DB connected).",
)
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict:
    # Verify DB connectivity
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
