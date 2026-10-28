"""Transaction status and account balance query endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.common import SuccessResponse
from app.schemas.query import AccountBalanceRequest, QueryResponse, TransactionStatusRequest
from app.services.mpesa_client import DarajaAPIError
from app.services.query import query_account_balance, query_transaction_status

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


@router.post(
    "/transaction-status",
    response_model=SuccessResponse[QueryResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Query Transaction Status",
    description="Query the status of any M-Pesa transaction by its transaction ID.",
    dependencies=[Depends(verify_api_key)],
)
async def transaction_status(
    request: TransactionStatusRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[QueryResponse]:
    try:
        result = await query_transaction_status(request, db)
        return SuccessResponse(
            message="Status query submitted. Result arrives via callback.",
            data=result,
        )
    except DarajaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )


@router.post(
    "/account-balance",
    response_model=SuccessResponse[QueryResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Query Account Balance",
    description="Query the M-Pesa account balance for a given shortcode.",
    dependencies=[Depends(verify_api_key)],
)
async def account_balance(
    request: AccountBalanceRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[QueryResponse]:
    try:
        result = await query_account_balance(request, db)
        return SuccessResponse(
            message="Balance query submitted. Result arrives via callback.",
            data=result,
        )
    except DarajaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Daraja API error", "daraja": exc.detail},
        )


@router.post(
    "/status-result",
    status_code=status.HTTP_200_OK,
    summary="Transaction Status Result Callback",
)
async def status_result(payload: dict) -> dict:
    logger.info("status_result_received", payload=payload)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post(
    "/balance-result",
    status_code=status.HTTP_200_OK,
    summary="Account Balance Result Callback",
)
async def balance_result(payload: dict) -> dict:
    logger.info("balance_result_received", payload=payload)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
