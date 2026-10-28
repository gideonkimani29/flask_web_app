"""STK Push API endpoints."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.common import SuccessResponse
from app.schemas.stk import STKCallback, STKPushRequest, STKPushResponse
from app.services.mpesa_client import DarajaAPIError
from app.services.stk import handle_stk_callback, initiate_stk_push

logger = get_logger(__name__)
router = APIRouter(prefix="/stk", tags=["STK Push"])


@router.post(
    "/push",
    response_model=SuccessResponse[STKPushResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate STK Push",
    description="Prompt a customer's phone to enter their M-Pesa PIN and pay.",
    dependencies=[Depends(verify_api_key)],
)
async def stk_push(
    request: STKPushRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[STKPushResponse]:
    try:
        result = await initiate_stk_push(request, db)
        return SuccessResponse(
            message="STK Push initiated. Customer will receive a prompt.",
            data=result,
        )
    except DarajaAPIError as exc:
        logger.error("stk_push_daraja_error", status_code=exc.status_code, detail=exc.detail)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )
    except Exception as exc:
        logger.exception("stk_push_unexpected_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.post(
    "/callback",
    status_code=status.HTTP_200_OK,
    summary="STK Push Callback (Safaricom → Service)",
    description=(
        "Receives the payment result from Safaricom. "
        "Must be a publicly accessible HTTPS URL registered with Daraja."
    ),
    include_in_schema=True,
)
async def stk_callback(
    callback: STKCallback,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Safaricom calls this endpoint with the STK push result.
    Processing happens in the background to return 200 immediately.
    """
    background_tasks.add_task(handle_stk_callback, callback, db)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
