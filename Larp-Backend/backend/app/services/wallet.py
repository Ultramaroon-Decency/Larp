"""Wallet abstraction and SimulationWallet implementation for autonomous x402 micropayments."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from app.core.logging import get_logger
from app.schemas.wallet import WalletRead, WalletTransaction

logger = get_logger("simulation_wallet")


class WalletInterface(ABC):
    """Abstract Wallet interface ensuring future EVM settlement compatibility."""

    @property
    @abstractmethod
    def address(self) -> str:
        """Return wallet address."""
        pass

    @abstractmethod
    async def get_balance(self) -> float:
        """Return current virtual balance in USD."""
        pass

    @abstractmethod
    async def get_available_balance(self) -> float:
        """Return uncommitted available balance in USD."""
        pass

    @abstractmethod
    async def get_total_spent(self) -> float:
        """Return total historical spent amount in USD."""
        pass

    @abstractmethod
    async def record_transaction(self, tx: WalletTransaction) -> WalletTransaction:
        """Record a new wallet transaction."""
        pass

    @abstractmethod
    async def get_transactions(self) -> List[WalletTransaction]:
        """Fetch transaction history."""
        pass

    @abstractmethod
    async def deduct_funds(self, amount: float, description: str = "") -> bool:
        """Atomically deduct funds if available."""
        pass


class SimulationWallet(WalletInterface):
    """Thread-safe Simulation Wallet operating in simulation mode without real funds moving."""

    def __init__(
        self,
        initial_balance: float = 1.00,
        address: Optional[str] = None,
    ) -> None:
        self._address = address or "0xSIMULATION_WALLET_7F8A9B"
        self._initial_balance = max(0.0, float(initial_balance))
        self._balance = self._initial_balance
        self._total_spent = 0.0
        self._transactions: List[WalletTransaction] = []
        self._lock = asyncio.Lock()

    @property
    def address(self) -> str:
        return self._address

    async def get_balance(self) -> float:
        async with self._lock:
            return round(self._balance, 4)

    async def get_available_balance(self) -> float:
        async with self._lock:
            return round(self._balance, 4)

    async def get_total_spent(self) -> float:
        async with self._lock:
            return round(self._total_spent, 4)

    async def record_transaction(self, tx: WalletTransaction) -> WalletTransaction:
        async with self._lock:
            # Ensure transaction clearly indicates simulation mode
            if not tx.transaction_id.startswith("sim_"):
                tx.transaction_id = f"sim_tx_{uuid4().hex[:12]}"
            tx.simulation = True
            tx.wallet_address = self._address
            self._transactions.append(tx)
            return tx

    async def get_transactions(self) -> List[WalletTransaction]:
        async with self._lock:
            return list(self._transactions)

    async def deduct_funds(self, amount: float, description: str = "") -> bool:
        """Atomically verify and deduct funds from wallet balance."""
        amount = round(amount, 4)
        if amount <= 0.0:
            return True

        async with self._lock:
            if self._balance < amount:
                logger.warning(
                    "SimulationWallet: Insufficient balance",
                    address=self._address,
                    required=amount,
                    balance=self._balance,
                )
                return False

            self._balance -= amount
            self._total_spent += amount
            logger.info(
                "SimulationWallet: Funds deducted",
                address=self._address,
                amount=amount,
                remaining_balance=round(self._balance, 4),
                description=description,
            )
            return True

    async def get_wallet_summary(self) -> WalletRead:
        """Return WalletRead summary model."""
        async with self._lock:
            return WalletRead(
                address=self._address,
                balance=round(self._balance, 4),
                available_balance=round(self._balance, 4),
                total_spent=round(self._total_spent, 4),
                transaction_count=len(self._transactions),
                simulation_mode=True,
                transactions=list(self._transactions),
            )
