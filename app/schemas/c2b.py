"""C2B (Customer-to-Business) schemas."""
from typing import Literal

from pydantic import BaseModel, Field


class C2BRegisterURLRequest(BaseModel):
    """Register validation and confirmation callback URLs."""

    shortcode: str = Field(..., description="Business shortcode")
    response_type: Literal["Completed", "Cancelled"] = Field(
        default="Completed",
        description="Response when validation URL is unreachable",
    )
    confirmation_url: str | None = Field(
        default=None, description="Override default confirmation URL"
    )
    validation_url: str | None = Field(
        default=None, description="Override default validation URL"
    )


class C2BSimulateRequest(BaseModel):
    """Simulate a C2B payment (sandbox only)."""

    shortcode: str = Field(..., description="Business shortcode")
    command_id: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"] = Field(
        default="CustomerPayBillOnline"
    )
    amount: int = Field(..., ge=1)
    msisdn: str = Field(..., description="Customer phone number 2547XXXXXXXX")
    bill_ref_number: str = Field(..., description="Account/bill reference")


class C2BValidationRequest(BaseModel):
    """Incoming C2B validation request from Safaricom."""

    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: str
    InvoiceNumber: str | None = None
    OrgAccountBalance: str | None = None
    ThirdPartyTransID: str | None = None
    MSISDN: str
    FirstName: str | None = None
    MiddleName: str | None = None
    LastName: str | None = None


class C2BConfirmationRequest(BaseModel):
    """Incoming C2B confirmation (final payment notice) from Safaricom."""

    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: str
    InvoiceNumber: str | None = None
    OrgAccountBalance: str | None = None
    ThirdPartyTransID: str | None = None
    MSISDN: str
    FirstName: str | None = None
    MiddleName: str | None = None
    LastName: str | None = None
