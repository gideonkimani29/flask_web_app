"""Transaction status and account balance query schemas."""
from typing import Literal

from pydantic import BaseModel, Field


class TransactionStatusRequest(BaseModel):
    """Request body to query a transaction's status."""

    transaction_id: str = Field(
        ..., description="M-Pesa transaction ID (e.g., LGR019G3J2)"
    )
    party_a: str | None = Field(
        default=None,
        description="Organization/phone querying. Defaults to B2C shortcode.",
    )
    identifier_type: Literal["1", "2", "4"] = Field(
        default="4",
        description="1=MSISDN, 2=Till Number, 4=Organization Shortcode",
    )
    remarks: str = Field(default="Status query", max_length=100)
    occasion: str = Field(default="", max_length=100)


class AccountBalanceRequest(BaseModel):
    """Request body to query account balance."""

    party_a: str | None = Field(
        default=None, description="Shortcode to query. Defaults to B2C shortcode."
    )
    identifier_type: Literal["1", "2", "4"] = Field(
        default="4",
        description="1=MSISDN, 2=Till Number, 4=Organization Shortcode",
    )
    remarks: str = Field(default="Balance query", max_length=100)


class QueryResponse(BaseModel):
    """Response from a query initiation."""

    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str
