"""
API Key security dependency.
All protected endpoints use Depends(verify_api_key).
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """
    Validate the X-API-Key request header.
    Raises HTTP 401 if missing, HTTP 403 if invalid.
    """
    settings = get_settings()

    if api_key is None:
        logger.warning("api_key_missing", detail="X-API-Key header not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.API_KEY:
        logger.warning("api_key_invalid", detail="Provided API key does not match")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key
