"""B2C (Business-to-Customer) schemas."""
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class B2CPaymentRequest(BaseModel):
    """Request body for a B2C payment."""

    phone_number: str = Field(
        ...,
        description="Recipient phone number 2547XXXXXXXX",
        examples=["254712345678"],
    )
    amount: int = Field(..., ge=1, description="Amount in KES")
    command_id: Literal[
        "SalaryPayment", "BusinessPayment", "PromotionPayment"
    ] = Field(default="BusinessPayment")
    remarks: str = Field(default="Payment", max_length=100)
    occasion: str = Field(default="", max_length=100)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace("+", "").replace(" ", "")
        if not v.startswith("254") or not v.isdigit() or len(v) not in (12, 13):
            raise ValueError("Phone number must start with 254 and be 12–13 digits")
        return v


class B2CPaymentResponse(BaseModel):
    """Response from a B2C payment initiation."""

    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str
    transaction_id: str | None = None


class B2CResultParameters(BaseModel):
    ResultParameter: list[dict[str, Any]] = []


class B2CReferenceData(BaseModel):
    ReferenceItem: dict[str, Any] | None = None


class B2CResultBody(BaseModel):
    ResultType: int
    ResultCode: int
    ResultDesc: str
    OriginatorConversationID: str
    ConversationID: str
    TransactionID: str
    ResultParameters: B2CResultParameters | None = None
    ReferenceData: B2CReferenceData | None = None


class B2CResult(BaseModel):
    """Full B2C result callback payload."""

    Result: B2CResultBody
