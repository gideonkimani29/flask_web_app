"""
Tests: C2B endpoints
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_c2b_validate_callback():
    """Validation callback must be publicly accessible — no API key required."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/c2b/validate",
            json={
                "TransactionType": "Pay Bill",
                "TransID": "LGR019G3J2",
                "TransTime": "20191219102115",
                "TransAmount": "10.00",
                "BusinessShortCode": "600638",
                "BillRefNumber": "account",
                "MSISDN": "254708374149",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ResultCode"] == 0


@pytest.mark.anyio
async def test_c2b_register_urls_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/c2b/register-urls",
            json={"shortcode": "600638"},
        )
    assert response.status_code == 401
