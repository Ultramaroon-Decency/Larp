"""Centralized Payment & Budget Decision Engine orchestrating simulation wallet, spending limits, idempotency, concurrency, and free tool fallbacks."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.core.logging import get_logger
from app.schemas.wallet import PaymentDecision, WalletRead, WalletTransaction
from app.services.tool_pricing import ToolPricingRegistry
from app.services.wallet import SimulationWallet, WalletInterface

logger = get_logger("payment_manager")


class PaymentManager:
    """Centralized Payment & Budget Decision Manager.
    
    Coordinates tool cost evaluation, wallet balance verification, research job budget tracking,
    spending limits (max single transaction, daily limits), idempotency retry protection,
    concurrency locks, and automatic free fallback tool selection.
    """

    def __init__(
        self,
        wallet: Optional[WalletInterface] = None,
        default_job_budget: float = 0.50,
        max_transaction_amount: float = 0.25,
        daily_spending_limit: float = 10.00,
        wallet_mode: str = "simulation",
    ) -> None:
        self.wallet = wallet or SimulationWallet(initial_balance=1.00)
        self.default_job_budget = default_job_budget
        self.max_transaction_amount = max_transaction_amount
        self.daily_spending_limit = daily_spending_limit
        self.wallet_mode = wallet_mode

        # Track per-job budget state: job_id -> {"allocated": float, "spent": float}
        self._job_budgets: Dict[str, Dict[str, float]] = {}
        # Track idempotency key -> PaymentDecision
        self._idempotency_cache: Dict[str, PaymentDecision] = {}
        # Daily tracking
        self._daily_spent: float = 0.0
        # Concurrency locks per job & global lock
        self._job_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def _get_job_lock(self, job_id: str) -> asyncio.Lock:
        if job_id not in self._job_locks:
            self._job_locks[job_id] = asyncio.Lock()
        return self._job_locks[job_id]

    def set_job_budget(self, job_id: str | UUID, budget: float) -> None:
        """Explicitly set or configure spending budget for a specific research job."""
        j_id = str(job_id)
        if j_id not in self._job_budgets:
            self._job_budgets[j_id] = {"allocated": round(budget, 4), "spent": 0.0}
        else:
            self._job_budgets[j_id]["allocated"] = round(budget, 4)

    def get_job_budget_summary(self, job_id: str | UUID) -> Dict[str, float]:
        """Get allocated, spent, and remaining budget for a research job."""
        j_id = str(job_id)
        if j_id not in self._job_budgets:
            self._job_budgets[j_id] = {"allocated": self.default_job_budget, "spent": 0.0}
        
        info = self._job_budgets[j_id]
        allocated = info["allocated"]
        spent = info["spent"]
        remaining = max(0.0, round(allocated - spent, 4))
        return {
            "allocated": allocated,
            "spent": spent,
            "remaining": remaining,
        }

    async def evaluate_and_settle(
        self,
        tool_name: str,
        job_id: Optional[str | UUID] = None,
        idempotency_key: Optional[str] = None,
    ) -> PaymentDecision:
        """Evaluate spending rules and execute simulated x402 payment settlement if approved.
        
        Rules Evaluated:
        1. Free Tool Bypass (cost == $0.00)
        2. Wallet Mode & Availability
        3. Single Transaction Limit
        4. Daily Spending Limit
        5. Wallet Available Balance
        6. Research Job Budget Remaining
        """
        j_id = str(job_id) if job_id else "global_job"
        cost = ToolPricingRegistry.get_tool_cost(tool_name)

        # ── Step 11: Idempotency Check (Prevent Double Charging on Retries) ──
        if idempotency_key:
            async with self._global_lock:
                if idempotency_key in self._idempotency_cache:
                    cached_decision = self._idempotency_cache[idempotency_key]
                    logger.info(
                        "PaymentManager: Idempotency cache hit — Returning existing decision",
                        idempotency_key=idempotency_key,
                        approved=cached_decision.approved,
                    )
                    return cached_decision

        # ── Step 12: Concurrency Lock per Research Job ────────────────────
        job_lock = self._get_job_lock(j_id)
        async with job_lock:
            # 1. Rule 1: Free Tool Bypass
            if cost <= 0.0:
                decision = PaymentDecision(
                    approved=True,
                    reason_code="FREE_TOOL",
                    reason=f"Tool '{tool_name}' is free ($0.00).",
                    amount=0.0,
                    tool=tool_name,
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # 2. Rule 2: Wallet Mode / Availability Check
            if not self.wallet:
                decision = self._reject_decision(
                    tool_name, cost, "WALLET_UNAVAILABLE", "Wallet is unavailable or uninitialized."
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # 3. Rule 3: Single Transaction Limit Check
            if cost > self.max_transaction_amount:
                reason_msg = f"Required cost ${cost:.2f} exceeds maximum single transaction limit of ${self.max_transaction_amount:.2f}."
                decision = self._reject_decision(
                    tool_name, cost, "COST_EXCEEDS_TRANSACTION_LIMIT", reason_msg
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # 4. Rule 4: Daily Spending Limit Check
            if (self._daily_spent + cost) > self.daily_spending_limit:
                reason_msg = f"Daily spending limit of ${self.daily_spending_limit:.2f} exceeded."
                decision = self._reject_decision(
                    tool_name, cost, "DAILY_LIMIT_EXCEEDED", reason_msg
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # 5. Rule 5: Wallet Balance Check
            wallet_balance = await self.wallet.get_available_balance()
            if cost > wallet_balance:
                reason_msg = f"Required payment is ${cost:.2f} but wallet balance is ${wallet_balance:.2f}."
                decision = self._reject_decision(
                    tool_name, cost, "INSUFFICIENT_BALANCE", reason_msg
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # 6. Rule 6: Research Job Budget Check
            budget_info = self.get_job_budget_summary(j_id)
            remaining_budget = budget_info["remaining"]
            if cost > remaining_budget:
                reason_msg = f"Required payment is ${cost:.2f} but research budget remaining is ${remaining_budget:.2f}."
                decision = self._reject_decision(
                    tool_name, cost, "INSUFFICIENT_RESEARCH_BUDGET", reason_msg
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # ── 7. Approval & x402 Simulated Settlement ──────────────────
            deducted = await self.wallet.deduct_funds(cost, description=f"Tool Micropayment: {tool_name}")
            if not deducted:
                decision = self._reject_decision(
                    tool_name, cost, "INSUFFICIENT_BALANCE", "Wallet fund deduction failed."
                )
                if idempotency_key:
                    self._idempotency_cache[idempotency_key] = decision
                return decision

            # Update job budget and daily spent atomically
            self._job_budgets[j_id]["spent"] += cost
            self._daily_spent += cost

            # Record simulated transaction with sim_tx_ prefix
            tx_id = f"sim_tx_{uuid4().hex[:12]}"
            tx = WalletTransaction(
                transaction_id=tx_id,
                wallet_address=self.wallet.address,
                amount=cost,
                currency="USD",
                tool=tool_name,
                status="success",
                timestamp=datetime.now(timezone.utc),
                research_job_id=j_id,
                reason_code="BUDGET_AVAILABLE",
                reason=f"Payment of ${cost:.2f} approved and settled.",
                simulation=True,
                idempotency_key=idempotency_key,
            )
            await self.wallet.record_transaction(tx)

            decision = PaymentDecision(
                approved=True,
                reason_code="BUDGET_AVAILABLE",
                reason=f"Payment of ${cost:.2f} is within available wallet and research budget.",
                amount=cost,
                tool=tool_name,
                transaction_id=tx_id,
            )

            # Log decision event
            logger.info(
                "tool_payment_decision",
                tool=tool_name,
                cost=cost,
                wallet_balance=round(wallet_balance - cost, 4),
                research_budget_remaining=round(remaining_budget - cost, 4),
                decision="approved",
                reason_code="BUDGET_AVAILABLE",
                transaction_id=tx_id,
            )

            if idempotency_key:
                self._idempotency_cache[idempotency_key] = decision

            return decision

    def _reject_decision(
        self, tool_name: str, cost: float, reason_code: str, reason: str
    ) -> PaymentDecision:
        """Construct rejection decision with structured reason and free fallback tool selection."""
        fallback = ToolPricingRegistry.get_free_fallback(tool_name)
        
        logger.warning(
            "tool_payment_decision",
            tool=tool_name,
            cost=cost,
            decision="rejected",
            reason_code=reason_code,
            reason=reason,
            fallback_tool=fallback,
        )

        return PaymentDecision(
            approved=False,
            reason_code=reason_code,
            reason=reason,
            amount=cost,
            tool=tool_name,
            fallback_tool=fallback,
        )

    async def get_wallet_summary(self) -> WalletRead:
        """Fetch current wallet status, balance, and transaction history."""
        if hasattr(self.wallet, "get_wallet_summary"):
            return await self.wallet.get_wallet_summary()
        
        balance = await self.wallet.get_balance()
        spent = await self.wallet.get_total_spent()
        txs = await self.wallet.get_transactions()
        return WalletRead(
            address=self.wallet.address,
            balance=balance,
            available_balance=balance,
            total_spent=spent,
            transaction_count=len(txs),
            simulation_mode=True,
            transactions=txs,
        )
