"""STK Push (Lipa Na M-Pesa Online) request/response schemas."""
from typing import Any

from pydantic import BaseModel, Field, field_validator


class STKPushRequest(BaseModel):
    """Request body for initiating an STK Push."""

    phone_number: str = Field(
        ...,
        description="Customer phone number in format 2547XXXXXXXX",
        examples=["254712345678"],
        min_length=12,
        max_length=13,
    )
    amount: int = Field(
        ...,
        description="Amount to charge in KES (whole numbers only)",
        ge=1,
        examples=[100],
    )
    account_reference: str = Field(
        ...,
        description="Account reference (alphanumeric, max 12 chars)",
        max_length=12,
        examples=["ORDER-001"],
    )
    transaction_desc: str = Field(
        default="Payment",
        description="Brief description of the transaction",
        max_length=13,
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace("+", "").replace(" ", "")
        if not v.startswith("254") or not v.isdigit() or len(v) not in (12, 13):
            raise ValueError(
                "Phone number must be in format 2547XXXXXXXX (12–13 digits, starting with 254)"
            )
        return v


class STKPushResponse(BaseModel):
    """Response from a successful STK Push initiation."""

    MerchantRequestID: str
    CheckoutRequestID: str
    ResponseCode: str
    ResponseDescription: str
    CustomerMessage: str

    # Internal tracking ID
    transaction_id: str | None = None


class STKQueryRequest(BaseModel):
    """Request body to query an STK Push transaction status."""

    checkout_request_id: str = Field(
        ..., description="CheckoutRequestID from the STK push initiation response"
    )


class STKCallbackMetadata(BaseModel):
    """Parsed metadata items from the STK callback."""

    Amount: float | None = None
    MpesaReceiptNumber: str | None = None
    TransactionDate: str | None = None
    PhoneNumber: str | None = None


class STKCallbackBody(BaseModel):
    """Body object within the STK Push callback payload."""

    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Any | None = None


class STKCallback(BaseModel):
    """Full STK Push callback payload from Safaricom."""

    Body: STKCallbackBody
