"""B2C service — Business-to-Customer payment disbursements."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import MpesaTransaction, TransactionStatus, TransactionType
from app.schemas.b2c import B2CPaymentRequest, B2CPaymentResponse, B2CResult
from app.services.mpesa_client import DarajaClient

logger = get_logger(__name__)


async def initiate_b2c_payment(
    request: B2CPaymentRequest, db: AsyncSession
) -> B2CPaymentResponse:
    """
    Initiate a B2C payment to a customer phone number.
    Persists the transaction record before and after the API call.
    """
    settings = get_settings()

    payload = {
        "InitiatorName": settings.MPESA_B2C_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_B2C_SECURITY_CREDENTIAL,
        "CommandID": request.command_id,
        "Amount": request.amount,
        "PartyA": settings.MPESA_B2C_SHORTCODE,
        "PartyB": request.phone_number,
        "Remarks": request.remarks,
        "QueueTimeOutURL": settings.MPESA_B2C_TIMEOUT_URL,
        "ResultURL": settings.MPESA_B2C_RESULT_URL,
        "Occasion": request.occasion,
    }

    txn = MpesaTransaction(
        transaction_type=TransactionType.B2C,
        status=TransactionStatus.PENDING,
        phone_number=request.phone_number,
        amount=request.amount,
        shortcode=settings.MPESA_B2C_SHORTCODE,
        description=request.remarks,
        request_payload=payload,
    )
    db.add(txn)
    await db.flush()

    logger.info(
        "b2c_payment_initiated",
        transaction_id=txn.id,
        phone=request.phone_number,
        amount=request.amount,
    )

    data = await DarajaClient.post(settings.b2c_url, payload)

    txn.conversation_id = data.get("ConversationID")
    txn.originator_conversation_id = data.get("OriginatorConversationID")
    txn.response_payload = data
    await db.flush()

    return B2CPaymentResponse(**data, transaction_id=txn.id)


async def handle_b2c_result(result: B2CResult, db: AsyncSession) -> None:
    """Process the B2C result callback from Safaricom."""
    body = result.Result

    stmt = select(MpesaTransaction).where(
        MpesaTransaction.conversation_id == body.ConversationID
    )
    res = await db.execute(stmt)
    txn: MpesaTransaction | None = res.scalar_one_or_none()

    if txn is None:
        logger.warning("b2c_result_unmatched", conversation_id=body.ConversationID)
        return

    txn.callback_payload = result.model_dump()

    if body.ResultCode == 0:
        txn.status = TransactionStatus.SUCCESS
        txn.mpesa_receipt_number = body.TransactionID
        logger.info(
            "b2c_result_success",
            transaction_id=txn.id,
            mpesa_txn_id=body.TransactionID,
        )
    else:
        txn.status = TransactionStatus.FAILED
        txn.error_code = str(body.ResultCode)
        txn.error_message = body.ResultDesc
        logger.warning(
            "b2c_result_failed",
            transaction_id=txn.id,
            result_code=body.ResultCode,
            result_desc=body.ResultDesc,
        )

    txn.completed_at = datetime.now(timezone.utc)
    await db.flush()
