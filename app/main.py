"""
FastAPI application factory.
Configures middleware, routers, error handlers, and startup/shutdown events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.models import Base
from app.db.session import engine
from app.middleware.logging import RequestLoggingMiddleware

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup; clean up on shutdown."""
    logger.info(
        "service_starting",
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.MPESA_ENVIRONMENT,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_ready")
    yield
    logger.info("service_shutting_down")
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready FastAPI service integrating the **Safaricom M-Pesa Daraja API**.\n\n"
            "## Authentication\n"
            "All endpoints (except Safaricom callbacks) require the `X-API-Key` header.\n\n"
            "## Supported APIs\n"
            "- **STK Push** — Lipa Na M-Pesa Online (customer-initiated)\n"
            "- **C2B** — Customer-to-Business URL registration & processing\n"
            "- **B2C** — Business-to-Customer disbursements\n"
            "- **Transaction Status** — Query any M-Pesa transaction\n"
            "- **Account Balance** — Query shortcode balance\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Exception Handlers ────────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("request_validation_error", errors=exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception("database_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred",
                },
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                },
            },
        )

    return app


app = create_app()
