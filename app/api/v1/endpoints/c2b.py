"""C2B API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.c2b import (
    C2BConfirmationRequest,
    C2BRegisterURLRequest,
    C2BSimulateRequest,
    C2BValidationRequest,
)
from app.schemas.common import SuccessResponse
from app.services.c2b import (
    handle_c2b_confirmation,
    handle_c2b_validation,
    register_urls,
    simulate_c2b,
)
from app.services.mpesa_client import DarajaAPIError

logger = get_logger(__name__)
router = APIRouter(prefix="/c2b", tags=["C2B"])


@router.post(
    "/register-urls",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Register C2B Callback URLs",
    dependencies=[Depends(verify_api_key)],
)
async def register_c2b_urls(request: C2BRegisterURLRequest) -> SuccessResponse[dict]:
    try:
        data = await register_urls(request)
        return SuccessResponse(message="URLs registered successfully", data=data)
    except DarajaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )


@router.post(
    "/simulate",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Simulate C2B Payment (Sandbox Only)",
    dependencies=[Depends(verify_api_key)],
)
async def simulate_payment(request: C2BSimulateRequest) -> SuccessResponse[dict]:
    try:
        data = await simulate_c2b(request)
        return SuccessResponse(message="C2B simulation triggered", data=data)
    except DarajaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )


@router.post(
    "/validate",
    status_code=status.HTTP_200_OK,
    summary="C2B Validation Callback (Safaricom → Service)",
    description="Safaricom calls this to validate a payment before it is processed.",
)
async def c2b_validate(request: C2BValidationRequest) -> dict:
    return await handle_c2b_validation(request)


@router.post(
    "/confirm",
    status_code=status.HTTP_200_OK,
    summary="C2B Confirmation Callback (Safaricom → Service)",
    description="Safaricom calls this to confirm a processed payment.",
)
async def c2b_confirm(
    request: C2BConfirmationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await handle_c2b_confirmation(request, db)
