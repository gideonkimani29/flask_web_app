"""B2C API endpoints."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.b2c import B2CPaymentRequest, B2CPaymentResponse, B2CResult
from app.schemas.common import SuccessResponse
from app.services.b2c import handle_b2c_result, initiate_b2c_payment
from app.services.mpesa_client import DarajaAPIError

logger = get_logger(__name__)
router = APIRouter(prefix="/b2c", tags=["B2C"])


@router.post(
    "/payment",
    response_model=SuccessResponse[B2CPaymentResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate B2C Payment",
    description="Disburse funds directly to a customer's M-Pesa wallet.",
    dependencies=[Depends(verify_api_key)],
)
async def b2c_payment(
    request: B2CPaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[B2CPaymentResponse]:
    try:
        result = await initiate_b2c_payment(request, db)
        return SuccessResponse(
            message="B2C payment initiated. Result will arrive via callback.",
            data=result,
        )
    except DarajaAPIError as exc:
        logger.error("b2c_daraja_error", status_code=exc.status_code, detail=exc.detail)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )
    except Exception as exc:
        logger.exception("b2c_unexpected_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.post(
    "/result",
    status_code=status.HTTP_200_OK,
    summary="B2C Result Callback (Safaricom → Service)",
    description="Safaricom calls this with the B2C payment result.",
)
async def b2c_result(
    result: B2CResult,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    background_tasks.add_task(handle_b2c_result, result, db)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post(
    "/timeout",
    status_code=status.HTTP_200_OK,
    summary="B2C Timeout Callback (Safaricom → Service)",
)
async def b2c_timeout(payload: dict) -> dict:
    logger.warning("b2c_timeout_received", payload=payload)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
