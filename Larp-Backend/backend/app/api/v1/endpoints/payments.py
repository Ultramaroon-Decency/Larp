"""Payments log endpoint for x402 payment receipts tracking."""

from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class PaymentsLogResponse(BaseModel):
    mode: str = "simulation"
    totalTransactions: int = 0
    totalSpentUSDC: str = "0.0000"
    receipts: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/log", summary="Get x402 Payments Log")
async def get_payments_log() -> PaymentsLogResponse:
    """Return summary of x402 autonomous payment receipts for Settings view."""
    return PaymentsLogResponse(
        mode="simulation",
        totalTransactions=0,
        totalSpentUSDC="0.0000",
        receipts=[],
    )
