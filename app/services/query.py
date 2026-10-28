"""Query service — transaction status and account balance."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import MpesaTransaction, TransactionStatus, TransactionType
from app.schemas.query import AccountBalanceRequest, QueryResponse, TransactionStatusRequest
from app.services.mpesa_client import DarajaClient

logger = get_logger(__name__)


async def query_transaction_status(
    request: TransactionStatusRequest, db: AsyncSession
) -> QueryResponse:
    """Query the status of an M-Pesa transaction via Daraja."""
    settings = get_settings()

    party_a = request.party_a or settings.MPESA_B2C_SHORTCODE

    payload = {
        "Initiator": settings.MPESA_B2C_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_B2C_SECURITY_CREDENTIAL,
        "CommandID": "TransactionStatusQuery",
        "TransactionID": request.transaction_id,
        "PartyA": party_a,
        "IdentifierType": request.identifier_type,
        "ResultURL": settings.MPESA_STATUS_RESULT_URL,
        "QueueTimeOutURL": settings.MPESA_STATUS_TIMEOUT_URL,
        "Remarks": request.remarks,
        "Occasion": request.occasion,
    }

    # Persist the query
    txn = MpesaTransaction(
        transaction_type=TransactionType.STATUS_QUERY,
        status=TransactionStatus.PENDING,
        mpesa_receipt_number=request.transaction_id,
        description=request.remarks,
        request_payload=payload,
    )
    db.add(txn)
    await db.flush()

    logger.info(
        "transaction_status_query",
        query_id=txn.id,
        mpesa_txn_id=request.transaction_id,
    )

    data = await DarajaClient.post(settings.transaction_status_url, payload)

    txn.conversation_id = data.get("ConversationID")
    txn.originator_conversation_id = data.get("OriginatorConversationID")
    txn.response_payload = data
    await db.flush()

    return QueryResponse(**data)


async def query_account_balance(
    request: AccountBalanceRequest, db: AsyncSession
) -> QueryResponse:
    """Query the account balance of a shortcode."""
    settings = get_settings()

    party_a = request.party_a or settings.MPESA_B2C_SHORTCODE

    payload = {
        "Initiator": settings.MPESA_B2C_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_B2C_SECURITY_CREDENTIAL,
        "CommandID": "AccountBalance",
        "PartyA": party_a,
        "IdentifierType": request.identifier_type,
        "Remarks": request.remarks,
        "QueueTimeOutURL": settings.MPESA_BALANCE_TIMEOUT_URL,
        "ResultURL": settings.MPESA_BALANCE_RESULT_URL,
    }

    txn = MpesaTransaction(
        transaction_type=TransactionType.BALANCE_QUERY,
        status=TransactionStatus.PENDING,
        shortcode=party_a,
        description=request.remarks,
        request_payload=payload,
    )
    db.add(txn)
    await db.flush()

    logger.info("account_balance_query", query_id=txn.id, shortcode=party_a)

    data = await DarajaClient.post(settings.account_balance_url, payload)

    txn.conversation_id = data.get("ConversationID")
    txn.originator_conversation_id = data.get("OriginatorConversationID")
    txn.response_payload = data
    await db.flush()

    return QueryResponse(**data)
