"""
M-Pesa Daraja OAuth2 token service.
Fetches and caches access tokens with automatic refresh before expiry.
"""
import asyncio
import base64
import time
from dataclasses import dataclass, field

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _TokenCache:
    access_token: str = ""
    expires_at: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def is_valid(self) -> bool:
        # Refresh 60 seconds before actual expiry
        return bool(self.access_token) and time.monotonic() < (self.expires_at - 60)


_cache = _TokenCache()


def _build_auth_header(consumer_key: str, consumer_secret: str) -> str:
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def get_access_token() -> str:
    """
    Return a valid Daraja OAuth access token.
    Uses an in-memory cache; fetches a fresh token only when needed.
    """
    async with _cache._lock:
        if _cache.is_valid():
            logger.debug("mpesa_token_cache_hit")
            return _cache.access_token

        settings = get_settings()
        auth_header = _build_auth_header(
            settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET
        )

        logger.info("mpesa_token_fetch", url=settings.oauth_url)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                settings.oauth_url,
                headers={"Authorization": auth_header},
            )
            response.raise_for_status()

        data = response.json()
        _cache.access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        _cache.expires_at = time.monotonic() + expires_in

        logger.info(
            "mpesa_token_refreshed",
            expires_in=expires_in,
            environment=settings.MPESA_ENVIRONMENT,
        )
        return _cache.access_token
