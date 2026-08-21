import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentRequirement(BaseModel):
    """
    Parsed details of an HTTP 402 Payment Required response.
    """
    resource_url: str = Field(..., description="Target API endpoint requiring payment.")
    price_amount: float = Field(..., description="Cost required for API execution.")
    currency: str = Field(default="USD", description="Currency or token symbol (e.g. USD, USDC, SATS).")
    payee_address: str = Field(..., description="Payment destination wallet or account address.")
    payment_nonce: str = Field(..., description="Unique payment challenge or transaction nonce.")
    scheme: str = Field(default="x402", description="Payment scheme protocol identifier.")


class PaymentReceipt(BaseModel):
    """
    Proof of payment authorization returned after successful settlement.
    """
    tx_id: str = Field(..., description="Unique transaction ID or payment proof hash.")
    payment_nonce: str = Field(..., description="Matching payment challenge nonce.")
    status: str = Field(default="settled", description="Payment status: 'settled', 'pending', or 'failed'.")
    authorization_header: str = Field(..., description="HTTP Header value to attach for authenticated retry.")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO timestamp of settlement."
    )


class PaymentTransaction(BaseModel):
    """
    Log record of an autonomous x402 payment event.
    """
    tx_id: str = Field(..., description="Unique transaction ID.")
    resource_url: str = Field(..., description="Target service URL.")
    amount: float = Field(..., description="Amount paid.")
    currency: str = Field(..., description="Currency used.")
    status: str = Field(..., description="Transaction status.")
    timestamp: str = Field(..., description="Timestamp.")
