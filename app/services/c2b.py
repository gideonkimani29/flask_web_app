"""C2B service — URL registration and inbound payment processing."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import MpesaTransaction, TransactionStatus, TransactionType
from app.schemas.c2b import (
    C2BConfirmationRequest,
    C2BRegisterURLRequest,
    C2BSimulateRequest,
    C2BValidationRequest,
)
from app.services.mpesa_client import DarajaClient

logger = get_logger(__name__)


async def register_urls(request: C2BRegisterURLRequest) -> dict:
    """Register C2B validation and confirmation callback URLs."""
    settings = get_settings()

    payload = {
        "ShortCode": request.shortcode,
        "ResponseType": request.response_type,
        "ConfirmationURL": request.confirmation_url or settings.MPESA_C2B_CONFIRMATION_URL,
        "ValidationURL": request.validation_url or settings.MPESA_C2B_VALIDATION_URL,
    }

    logger.info("c2b_register_urls", shortcode=request.shortcode)
    return await DarajaClient.post(settings.c2b_register_url, payload)


async def simulate_c2b(request: C2BSimulateRequest) -> dict:
    """Simulate a C2B transaction (sandbox only)."""
    settings = get_settings()

    payload = {
        "ShortCode": request.shortcode,
        "CommandID": request.command_id,
        "Amount": request.amount,
        "Msisdn": request.msisdn,
        "BillRefNumber": request.bill_ref_number,
    }

    logger.info("c2b_simulate", shortcode=request.shortcode, amount=request.amount)
    return await DarajaClient.post(settings.c2b_simulate_url, payload)


async def handle_c2b_validation(
    request: C2BValidationRequest,
) -> dict:
    """
    Handle incoming C2B validation request.
    Return ResultCode=0 to accept; non-zero to reject.
    Add custom business logic here (e.g., verify account number).
    """
    logger.info(
        "c2b_validation_received",
        trans_id=request.TransID,
        msisdn=request.MSISDN,
        amount=request.TransAmount,
        bill_ref=request.BillRefNumber,
    )
    # TODO: Add account lookup / validation logic
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


async def handle_c2b_confirmation(
    request: C2BConfirmationRequest, db: AsyncSession
) -> dict:
    """
    Process a confirmed C2B payment — persist to the transaction ledger.
    """
    txn = MpesaTransaction(
        transaction_type=TransactionType.C2B,
        status=TransactionStatus.SUCCESS,
        phone_number=request.MSISDN,
        amount=float(request.TransAmount),
        shortcode=request.BusinessShortCode,
        reference=request.BillRefNumber,
        mpesa_receipt_number=request.TransID,
        callback_payload=request.model_dump(),
    )
    db.add(txn)
    await db.flush()

    logger.info(
        "c2b_confirmation_processed",
        transaction_id=txn.id,
        trans_id=request.TransID,
        amount=request.TransAmount,
        msisdn=request.MSISDN,
    )
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
