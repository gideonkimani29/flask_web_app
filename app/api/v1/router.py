"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import b2c, c2b, health, query, stk

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(stk.router)
api_router.include_router(c2b.router)
api_router.include_router(b2c.router)
api_router.include_router(query.router)
