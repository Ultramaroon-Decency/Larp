"""
Algorand x402 Payment Service for Research Pipeline.

Sends real USDC (ASA 10458941) micropayments on Algorand Testnet for each
research pipeline step. Transactions are verifiable on Lora Explorer.

Usage:
    from app.services.algorand_x402 import AlgorandX402PaymentService
    payment_svc = AlgorandX402PaymentService()
    receipt = await payment_svc.pay_for_step("PlannerAgent", 0.0008)
"""

import os
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("algorand_x402")

# ── Constants ──────────────────────────────────────────────────────────────────
USDC_ASA_ID = 10458941  # Algorand Testnet USDC
ALGOD_URL = "https://testnet-api.algonode.cloud"
LORA_EXPLORER_BASE = "https://lora.algokit.io/testnet/transaction"


@dataclass
class PaymentReceipt:
    """Receipt for a single x402 micropayment on Algorand Testnet."""
    step_name: str
    amount_usdc: float
    tx_hash: str
    from_address: str
    to_address: str
    explorer_url: str
    timestamp: str
    is_real: bool = True  # False for simulation mode


@dataclass
class AlgorandX402PaymentService:
    """
    Manages x402 micropayments on Algorand Testnet.
    
    Reads ALGORAND_AGENT_MNEMONIC and AVM_ADDRESS from environment.
    If mnemonic is not set, operates in simulation mode.
    """
    _account: Optional[object] = field(default=None, init=False, repr=False)
    _receiver: str = field(default="", init=False)
    _is_simulation: bool = field(default=True, init=False)
    _receipts: list = field(default_factory=list, init=False)

    def __post_init__(self):
        mnemonic = os.getenv("ALGORAND_AGENT_MNEMONIC", "")
        self._receiver = os.getenv("AVM_ADDRESS", "")

        if mnemonic and len(mnemonic.split()) == 25:
            try:
                from algosdk import mnemonic as alg_mnemonic, account
                private_key = alg_mnemonic.to_private_key(mnemonic)
                address = account.address_from_private_key(private_key)
                self._account = {
                    "private_key": private_key,
                    "address": address,
                }
                self._is_simulation = False
                logger.info(f"[x402] ✓ Real Algorand wallet: {address}")
            except Exception as e:
                logger.warning(f"[x402] Failed to load wallet: {e}")
                self._is_simulation = True
        else:
            logger.info("[x402] ⚠ Simulation mode (no ALGORAND_AGENT_MNEMONIC)")

    @property
    def is_simulation(self) -> bool:
        return self._is_simulation

    @property
    def receipts(self) -> list:
        return list(self._receipts)

    @property
    def total_cost(self) -> float:
        return sum(r.amount_usdc for r in self._receipts)

    async def pay_for_step(self, step_name: str, cost_usd: float) -> PaymentReceipt:
        """
        Execute a USDC micropayment for a pipeline step.
        
        In real mode: sends an ASA transfer on Algorand Testnet.
        In simulation mode: generates a mock receipt.
        """
        if not self._is_simulation and self._account and self._receiver:
            return await self._real_payment(step_name, cost_usd)
        else:
            return self._simulated_payment(step_name, cost_usd)

    async def _real_payment(self, step_name: str, cost_usd: float) -> PaymentReceipt:
        """Send a real USDC ASA transfer on Algorand Testnet."""
        try:
            from algosdk.v2client import algod
            from algosdk import transaction
            from algosdk.transaction import wait_for_confirmation

            client = algod.AlgodClient("", ALGOD_URL)
            params = client.suggested_params()

            # USDC has 6 decimal places
            amount_micro = int(cost_usd * 1_000_000)

            txn = transaction.AssetTransferTxn(
                sender=self._account["address"],
                sp=params,
                receiver=self._receiver,
                amt=amount_micro,
                index=USDC_ASA_ID,
            )

            signed_txn = txn.sign(self._account["private_key"])

            # Run the blocking algod calls in a thread to not block the event loop
            loop = asyncio.get_event_loop()
            tx_id = await loop.run_in_executor(
                None, lambda: client.send_transaction(signed_txn)
            )

            logger.info(f"[x402] USDC transfer submitted: {tx_id}")

            # Wait for confirmation (run in thread)
            await loop.run_in_executor(
                None, lambda: wait_for_confirmation(client, tx_id, 4)
            )

            logger.info(f"[x402] ✓ Confirmed on Algorand Testnet: {tx_id}")

            receipt = PaymentReceipt(
                step_name=step_name,
                amount_usdc=cost_usd,
                tx_hash=tx_id,
                from_address=self._account["address"],
                to_address=self._receiver,
                explorer_url=f"{LORA_EXPLORER_BASE}/{tx_id}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                is_real=True,
            )
            self._receipts.append(receipt)
            return receipt

        except Exception as e:
            logger.error(f"[x402] Payment failed for {step_name}: {e}")
            # Fall back to simulation on failure
            return self._simulated_payment(step_name, cost_usd)

    def _simulated_payment(self, step_name: str, cost_usd: float) -> PaymentReceipt:
        """Generate a simulated payment receipt."""
        import hashlib
        import time

        fake_hash = hashlib.sha256(
            f"{step_name}-{time.time()}".encode()
        ).hexdigest()[:52].upper()

        from_addr = self._account["address"] if self._account else "SIM_AGENT_ADDRESS"
        to_addr = self._receiver or "SIM_MERCHANT_ADDRESS"

        receipt = PaymentReceipt(
            step_name=step_name,
            amount_usdc=cost_usd,
            tx_hash=fake_hash,
            from_address=from_addr,
            to_address=to_addr,
            explorer_url=f"{LORA_EXPLORER_BASE}/{fake_hash}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            is_real=False,
        )
        self._receipts.append(receipt)
        return receipt
