"""Wallet and research budget status endpoint."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_payment_manager
from app.schemas.common import ResponseEnvelope
from app.schemas.wallet import WalletRead
from app.services.payment_manager import PaymentManager

router = APIRouter()


@router.get(
    "/",
    summary="Get Simulation Wallet & Research Budget Status",
    response_model=ResponseEnvelope[WalletRead],
    status_code=status.HTTP_200_OK,
)
async def get_wallet_status(
    current_user: dict = Depends(get_current_user),
    payment_manager: PaymentManager = Depends(get_payment_manager),
) -> ResponseEnvelope[WalletRead]:
    """Retrieve simulation wallet status, virtual balance, remaining research budget, and transaction logs."""
    wallet_summary = await payment_manager.get_wallet_summary()
    return ResponseEnvelope(
        success=True,
        message="Wallet and research budget status retrieved successfully",
        data=wallet_summary,
    )
