"""
Low-level Daraja API HTTP client.
All service modules use this client to make authenticated requests.
"""
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.logging import get_logger
from app.services.auth import get_access_token

logger = get_logger(__name__)

_TIMEOUT = httpx.Timeout(timeout=30.0, connect=10.0)


class DarajaAPIError(Exception):
    """Raised when Daraja API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Daraja API error {status_code}: {detail}")


class DarajaClient:
    """
    Authenticated async HTTP client for the Safaricom Daraja API.
    Automatically injects Bearer tokens and handles retries.
    """

    @staticmethod
    async def _get_headers() -> dict[str, str]:
        token = await get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        POST JSON payload to Daraja endpoint.
        Retries up to 3 times on network errors with exponential backoff.
        """
        headers = await DarajaClient._get_headers()

        logger.info("daraja_request", method="POST", url=url, payload=payload)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)

        data = response.json()
        logger.info(
            "daraja_response",
            method="POST",
            url=url,
            status_code=response.status_code,
            body=data,
        )

        if response.status_code not in (200, 201):
            raise DarajaAPIError(status_code=response.status_code, detail=data)

        return data

    @staticmethod
    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def get(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        GET request to Daraja endpoint.
        Retries up to 3 times on network errors with exponential backoff.
        """
        headers = await DarajaClient._get_headers()

        logger.info("daraja_request", method="GET", url=url, params=params)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, params=params, headers=headers)

        data = response.json()
        logger.info(
            "daraja_response",
            method="GET",
            url=url,
            status_code=response.status_code,
            body=data,
        )

        if response.status_code not in (200, 201):
            raise DarajaAPIError(status_code=response.status_code, detail=data)

        return data
