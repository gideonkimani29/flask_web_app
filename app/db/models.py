"""Database models for M-Pesa transaction audit trail."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TransactionType(str, PyEnum):
    STK_PUSH = "STK_PUSH"
    C2B = "C2B"
    B2C = "B2C"
    BALANCE_QUERY = "BALANCE_QUERY"
    STATUS_QUERY = "STATUS_QUERY"


class TransactionStatus(str, PyEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class MpesaTransaction(Base):
    """Stores all M-Pesa transaction requests and their outcomes."""

    __tablename__ = "mpesa_transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False, index=True
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )

    # Daraja identifiers
    merchant_request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    checkout_request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    originator_conversation_id: Mapped[str | None] = mapped_column(String(100))
    mpesa_receipt_number: Mapped[str | None] = mapped_column(String(50))

    # Payment details
    phone_number: Mapped[str | None] = mapped_column(String(20))
    amount: Mapped[float | None] = mapped_column(Float)
    shortcode: Mapped[str | None] = mapped_column(String(20))
    reference: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))

    # Raw payloads for audit
    request_payload: Mapped[dict | None] = mapped_column(JSON)
    response_payload: Mapped[dict | None] = mapped_column(JSON)
    callback_payload: Mapped[dict | None] = mapped_column(JSON)

    # Error tracking
    error_code: Mapped[str | None] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<MpesaTransaction id={self.id} type={self.transaction_type} "
            f"status={self.status} amount={self.amount}>"
        )
