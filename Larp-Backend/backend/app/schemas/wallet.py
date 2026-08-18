"""Pydantic schemas for Autonomous x402 Budget & Simulation Wallet."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class WalletTransaction(BaseModel):
    """Transaction record for simulated or EVM x402 tool micropayments."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str = Field(
        default_factory=lambda: f"sim_tx_{uuid4().hex[:12]}",
        description="Unique transaction ID. Simulated transactions always start with 'sim_tx_'.",
    )
    wallet_address: str = Field(description="Wallet address initiating payment")
    amount: float = Field(ge=0.0, description="Payment amount in USD")
    currency: str = Field(default="USD", description="Payment currency code")
    tool: str = Field(description="Paid tool or API name requested")
    status: str = Field(default="success", description="Transaction status: 'success', 'rejected', 'failed'")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Transaction creation timestamp",
    )
    research_job_id: Optional[str] = Field(default=None, description="Associated research job UUID string")
    reason_code: Optional[str] = Field(default=None, description="Machine-readable decision or skip reason code")
    reason: Optional[str] = Field(default=None, description="Human-readable explanation statement")
    simulation: bool = Field(default=True, description="Flag indicating simulation mode transaction")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key to prevent double charging")


class PaymentDecision(BaseModel):
    """Structured decision output from PaymentManager decision engine."""

    approved: bool = Field(description="Approval flag")
    reason_code: str = Field(description="Machine-readable reason code")
    reason: str = Field(description="Human-readable explanation")
    amount: float = Field(default=0.0, ge=0.0, description="Cost amount in USD")
    tool: str = Field(description="Requested tool name")
    fallback_tool: Optional[str] = Field(default=None, description="Name of free alternative tool if rejected")
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID if approved and settled")


class WalletRead(BaseModel):
    """Wallet status and metrics response model."""

    model_config = ConfigDict(from_attributes=True)

    address: str = Field(description="Wallet address")
    balance: float = Field(ge=0.0, description="Total virtual wallet balance in USD")
    available_balance: float = Field(ge=0.0, description="Available uncommitted balance in USD")
    total_spent: float = Field(ge=0.0, description="Total historical spending in USD")
    transaction_count: int = Field(ge=0, description="Total number of transactions recorded")
    simulation_mode: bool = Field(default=True, description="Flag indicating whether simulation mode is active")
    transactions: List[WalletTransaction] = Field(default_factory=list, description="Recent transaction history")
