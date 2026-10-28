"""
STK Push service — business logic for Lipa Na M-Pesa Online.
Generates the required password/timestamp and calls the Daraja API.
"""
import base64
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import MpesaTransaction, TransactionStatus, TransactionType
from app.schemas.stk import STKCallback, STKPushRequest, STKPushResponse
from app.services.mpesa_client import DarajaClient

logger = get_logger(__name__)


def _generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """Generate the base64-encoded Daraja STK password."""
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def _get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


async def initiate_stk_push(
    request: STKPushRequest, db: AsyncSession
) -> STKPushResponse:
    """
    Build and send an STK Push request to Daraja.
    Persists the transaction to the database before and after the API call.
    """
    settings = get_settings()
    timestamp = _get_timestamp()
    shortcode = settings.MPESA_LIPA_NA_MPESA_SHORTCODE
    password = _generate_password(shortcode, settings.MPESA_LIPA_NA_MPESA_PASSKEY, timestamp)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": request.amount,
        "PartyA": request.phone_number,
        "PartyB": shortcode,
        "PhoneNumber": request.phone_number,
        "CallBackURL": settings.MPESA_STK_CALLBACK_URL,
        "AccountReference": request.account_reference,
        "TransactionDesc": request.transaction_desc,
    }

    # Persist pending transaction
    txn = MpesaTransaction(
        transaction_type=TransactionType.STK_PUSH,
        status=TransactionStatus.PENDING,
        phone_number=request.phone_number,
        amount=request.amount,
        reference=request.account_reference,
        description=request.transaction_desc,
        request_payload=payload,
    )
    db.add(txn)
    await db.flush()

    logger.info("stk_push_initiated", transaction_id=txn.id, phone=request.phone_number)

    data = await DarajaClient.post(settings.stk_push_url, payload)

    # Update transaction with Daraja identifiers
    txn.merchant_request_id = data.get("MerchantRequestID")
    txn.checkout_request_id = data.get("CheckoutRequestID")
    txn.response_payload = data

    await db.flush()

    return STKPushResponse(
        **data,
        transaction_id=txn.id,
    )


async def handle_stk_callback(callback: STKCallback, db: AsyncSession) -> None:
    """
    Process an incoming STK Push callback from Safaricom.
    Updates the stored transaction record with the result.
    """
    body = callback.Body
    from sqlalchemy import select

    result = await db.execute(
        select(MpesaTransaction).where(
            MpesaTransaction.checkout_request_id == body.CheckoutRequestID
        )
    )
    txn: MpesaTransaction | None = result.scalar_one_or_none()

    if txn is None:
        logger.warning(
            "stk_callback_unmatched",
            checkout_request_id=body.CheckoutRequestID,
        )
        return

    txn.callback_payload = callback.model_dump()

    if body.ResultCode == 0:
        txn.status = TransactionStatus.SUCCESS
        # Parse metadata
        if body.CallbackMetadata:
            items = body.CallbackMetadata.get("Item", [])
            meta = {item["Name"]: item.get("Value") for item in items}
            txn.mpesa_receipt_number = meta.get("MpesaReceiptNumber")
            txn.amount = meta.get("Amount", txn.amount)
        logger.info(
            "stk_callback_success",
            transaction_id=txn.id,
            receipt=txn.mpesa_receipt_number,
        )
    else:
        txn.status = TransactionStatus.FAILED
        txn.error_code = str(body.ResultCode)
        txn.error_message = body.ResultDesc
        logger.warning(
            "stk_callback_failed",
            transaction_id=txn.id,
            result_code=body.ResultCode,
            result_desc=body.ResultDesc,
        )

    from datetime import datetime, timezone
    txn.completed_at = datetime.now(timezone.utc)
    await db.flush()
