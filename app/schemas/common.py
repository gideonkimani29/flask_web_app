"""Common shared schemas for API responses."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
    correlation_id: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    correlation_id: str | None = None


class MpesaBaseResponse(BaseModel):
    """Base for raw Daraja API responses."""

    ResponseCode: str | None = None
    ResponseDescription: str | None = None
    CustomerMessage: str | None = None
