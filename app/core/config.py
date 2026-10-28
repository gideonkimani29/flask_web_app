"""
Core application settings using pydantic-settings.
All values are loaded from environment variables / .env file.
"""
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "MPesa Daraja Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_KEY: str = Field(..., description="API key for authenticating callers")

    # ── M-Pesa Daraja ────────────────────────────────────────────────────
    MPESA_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"
    MPESA_CONSUMER_KEY: str = Field(..., description="Daraja consumer key")
    MPESA_CONSUMER_SECRET: str = Field(..., description="Daraja consumer secret")

    # STK Push / Lipa Na M-Pesa
    MPESA_SHORTCODE: str = "174379"
    MPESA_LIPA_NA_MPESA_SHORTCODE: str = "174379"
    MPESA_LIPA_NA_MPESA_PASSKEY: str = Field(..., description="LNM passkey")

    # B2C
    MPESA_B2C_SHORTCODE: str = "600986"
    MPESA_B2C_INITIATOR_NAME: str = "testapi"
    MPESA_B2C_SECURITY_CREDENTIAL: str = ""

    # Callback URLs
    MPESA_STK_CALLBACK_URL: str = "https://example.com/api/v1/stk/callback"
    MPESA_C2B_VALIDATION_URL: str = "https://example.com/api/v1/c2b/validate"
    MPESA_C2B_CONFIRMATION_URL: str = "https://example.com/api/v1/c2b/confirm"
    MPESA_B2C_RESULT_URL: str = "https://example.com/api/v1/b2c/result"
    MPESA_B2C_TIMEOUT_URL: str = "https://example.com/api/v1/b2c/timeout"
    MPESA_BALANCE_RESULT_URL: str = "https://example.com/api/v1/query/balance-result"
    MPESA_BALANCE_TIMEOUT_URL: str = "https://example.com/api/v1/query/balance-timeout"
    MPESA_STATUS_RESULT_URL: str = "https://example.com/api/v1/query/status-result"
    MPESA_STATUS_TIMEOUT_URL: str = "https://example.com/api/v1/query/status-timeout"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./mpesa.db"

    # ── Logging ──────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # ── Derived properties ───────────────────────────────────────────────
    @property
    def daraja_base_url(self) -> str:
        if self.MPESA_ENVIRONMENT == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    @property
    def oauth_url(self) -> str:
        return f"{self.daraja_base_url}/oauth/v1/generate?grant_type=client_credentials"

    @property
    def stk_push_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/stkpush/v1/processrequest"

    @property
    def stk_query_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/stkpushquery/v1/query"

    @property
    def c2b_register_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/c2b/v1/registerurl"

    @property
    def c2b_simulate_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/c2b/v1/simulate"

    @property
    def b2c_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/b2c/v1/paymentrequest"

    @property
    def transaction_status_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/transactionstatus/v1/query"

    @property
    def account_balance_url(self) -> str:
        return f"{self.daraja_base_url}/mpesa/accountbalance/v1/query"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
