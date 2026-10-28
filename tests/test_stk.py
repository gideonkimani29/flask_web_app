"""
Tests: STK Push endpoints
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_stk_push_missing_api_key():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/stk/push",
            json={
                "phone_number": "254712345678",
                "amount": 100,
                "account_reference": "TEST-001",
            },
        )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_stk_push_invalid_phone():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/stk/push",
            headers={"X-API-Key": "test-key"},
            json={
                "phone_number": "0712345678",  # invalid format
                "amount": 100,
                "account_reference": "TEST-001",
            },
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_stk_push_zero_amount():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/stk/push",
            headers={"X-API-Key": "test-key"},
            json={
                "phone_number": "254712345678",
                "amount": 0,
                "account_reference": "TEST-001",
            },
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
