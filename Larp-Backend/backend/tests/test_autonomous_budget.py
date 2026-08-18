"""Comprehensive unit test suite for Autonomous x402 Budget & Simulation Wallet system."""

import asyncio
import pytest
from uuid import uuid4

from app.schemas.wallet import PaymentDecision, WalletRead, WalletTransaction
from app.services.wallet import SimulationWallet
from app.services.tool_pricing import ToolPricingRegistry
from app.services.payment_manager import PaymentManager
from app.services.agent_manager import AgentManager


@pytest.mark.asyncio
async def test_1_wallet_initializes_with_configured_balance():
    """Requirement 1: SimulationWallet initializes with configured balance."""
    wallet = SimulationWallet(initial_balance=1.00)
    assert wallet.address.startswith("0xSIMULATION")
    assert await wallet.get_balance() == 1.00
    assert await wallet.get_total_spent() == 0.0


@pytest.mark.asyncio
async def test_2_successful_simulated_payment():
    """Requirement 2: Approved simulated payment returns approved decision."""
    pm = PaymentManager(
        wallet=SimulationWallet(initial_balance=1.00),
        default_job_budget=0.50,
        max_transaction_amount=0.25,
    )
    decision = await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id="job123")
    assert decision.approved is True
    assert decision.reason_code == "BUDGET_AVAILABLE"
    assert decision.amount == 0.15
    assert decision.transaction_id.startswith("sim_tx_")


@pytest.mark.asyncio
async def test_3_balance_decreases_correctly():
    """Requirement 3: Wallet balance decreases correctly after payment settlement."""
    wallet = SimulationWallet(initial_balance=1.00)
    pm = PaymentManager(wallet=wallet, default_job_budget=0.50)
    
    await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id="job123") # $0.15
    assert await wallet.get_balance() == 0.85
    assert await wallet.get_total_spent() == 0.15


@pytest.mark.asyncio
async def test_4_research_budget_decreases_correctly():
    """Requirement 4: Job-level research budget decreases correctly after payment."""
    pm = PaymentManager(default_job_budget=0.50)
    job_id = str(uuid4())
    
    await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id=job_id) # $0.15
    budget_summary = pm.get_job_budget_summary(job_id)
    assert budget_summary["allocated"] == 0.50
    assert budget_summary["spent"] == 0.15
    assert budget_summary["remaining"] == 0.35


@pytest.mark.asyncio
async def test_5_insufficient_wallet_balance_rejected():
    """Requirement 5: Rejection when wallet balance is lower than required payment."""
    wallet = SimulationWallet(initial_balance=0.10) # Wallet has $0.10
    pm = PaymentManager(wallet=wallet, default_job_budget=0.50)
    
    decision = await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id="job123") # $0.15
    assert decision.approved is False
    assert decision.reason_code == "INSUFFICIENT_BALANCE"
    assert "required payment is $0.15" in decision.reason.lower()
    assert decision.fallback_tool == "SearchTool"


@pytest.mark.asyncio
async def test_6_insufficient_research_budget_rejected():
    """Requirement 6: Rejection when research job budget is lower than required payment."""
    wallet = SimulationWallet(initial_balance=10.00) # Wallet has plenty of funds
    pm = PaymentManager(wallet=wallet, default_job_budget=0.10) # Job budget is only $0.10
    job_id = str(uuid4())
    
    decision = await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id=job_id) # $0.15
    assert decision.approved is False
    assert decision.reason_code == "INSUFFICIENT_RESEARCH_BUDGET"
    assert decision.fallback_tool == "SearchTool"


@pytest.mark.asyncio
async def test_7_transaction_limit_exceeded_rejected():
    """Requirement 7: Rejection when cost exceeds single transaction limit ($0.25)."""
    wallet = SimulationWallet(initial_balance=10.00)
    pm = PaymentManager(wallet=wallet, default_job_budget=5.00, max_transaction_amount=0.25)
    
    decision = await pm.evaluate_and_settle(tool_name="ExpensiveAnalysisTool", job_id="job123") # $0.30
    assert decision.approved is False
    assert decision.reason_code == "COST_EXCEEDS_TRANSACTION_LIMIT"
    assert "exceeds maximum single transaction limit" in decision.reason.lower()


@pytest.mark.asyncio
async def test_8_correct_skip_reason_recorded():
    """Requirement 8: Structured skip reason code and explanation are recorded."""
    wallet = SimulationWallet(initial_balance=0.05)
    pm = PaymentManager(wallet=wallet)
    
    decision = await pm.evaluate_and_settle(tool_name="AcademicPremiumTool", job_id="job123") # $0.10
    assert decision.approved is False
    assert decision.reason_code == "INSUFFICIENT_BALANCE"
    assert decision.reason is not None


@pytest.mark.asyncio
async def test_9_free_fallback_executes_after_rejected_paid_tool():
    """Requirement 9: Free fallback tool is automatically identified when paid tool is rejected."""
    pm = PaymentManager(default_job_budget=0.05) # Budget too low for $0.15 tool
    decision = await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id="job123")
    
    assert decision.approved is False
    assert decision.fallback_tool == "SearchTool"
    # Ensure fallback tool is free
    assert ToolPricingRegistry.get_tool_cost(decision.fallback_tool) == 0.00


@pytest.mark.asyncio
async def test_10_transaction_history_recorded():
    """Requirement 10: Wallet transaction history records settled payments."""
    wallet = SimulationWallet(initial_balance=1.00)
    pm = PaymentManager(wallet=wallet)
    
    await pm.evaluate_and_settle(tool_name="PremiumSearchTool", job_id="job1") # $0.15
    await pm.evaluate_and_settle(tool_name="AcademicPremiumTool", job_id="job2") # $0.10
    
    txs = await wallet.get_transactions()
    assert len(txs) == 2
    assert txs[0].tool == "PremiumSearchTool"
    assert txs[1].tool == "AcademicPremiumTool"


@pytest.mark.asyncio
async def test_11_simulation_transaction_clearly_marked():
    """Requirement 11: Transaction ID starts with 'sim_tx_' and has simulation=True flag."""
    wallet = SimulationWallet(initial_balance=1.00)
    pm = PaymentManager(wallet=wallet)
    
    decision = await pm.evaluate_and_settle(tool_name="DeepFactCheckTool", job_id="job123")
    assert decision.transaction_id.startswith("sim_tx_")
    
    txs = await wallet.get_transactions()
    assert txs[0].simulation is True
    assert txs[0].transaction_id.startswith("sim_tx_")


@pytest.mark.asyncio
async def test_12_payment_retry_idempotency_prevents_double_charging():
    """Requirement 12: Retrying with the same idempotency key does not deduct budget twice."""
    wallet = SimulationWallet(initial_balance=1.00)
    pm = PaymentManager(wallet=wallet, default_job_budget=0.50)
    idempotency_key = "retry_key_999"
    
    dec1 = await pm.evaluate_and_settle("PremiumSearchTool", job_id="job1", idempotency_key=idempotency_key)
    assert dec1.approved is True
    assert await wallet.get_balance() == 0.85
    
    # Retry payment with exact same idempotency key
    dec2 = await pm.evaluate_and_settle("PremiumSearchTool", job_id="job1", idempotency_key=idempotency_key)
    assert dec2.approved is True
    # Balance must remain 0.85 (not 0.70!)
    assert await wallet.get_balance() == 0.85


@pytest.mark.asyncio
async def test_13_concurrent_payments_cannot_overspend_budget():
    """Requirement 13: Concurrency protection prevents simultaneous requests from overspending budget."""
    wallet = SimulationWallet(initial_balance=1.00)
    # Research budget is $0.20 (enough for ONLY ONE $0.15 tool request)
    pm = PaymentManager(wallet=wallet, default_job_budget=0.20)
    job_id = "concurrent_job_123"
    
    # Trigger 3 simultaneous tool payment requests of $0.15 each
    tasks = [
        pm.evaluate_and_settle("PremiumSearchTool", job_id=job_id)
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)
    
    approved_count = sum(1 for r in results if r.approved)
    rejected_count = sum(1 for r in results if not r.approved)
    
    # Exactly 1 request must be approved, and 2 rejected
    assert approved_count == 1
    assert rejected_count == 2
    
    budget_summary = pm.get_job_budget_summary(job_id)
    assert budget_summary["spent"] == 0.15
    assert budget_summary["remaining"] == 0.05


@pytest.mark.asyncio
async def test_14_zero_cost_free_tools_bypass_payment_logic():
    """Requirement 14: Zero-cost ($0.00) tools bypass payment and return FREE_TOOL code."""
    pm = PaymentManager(default_job_budget=0.0) # Zero budget
    decision = await pm.evaluate_and_settle(tool_name="SearchTool", job_id="job1")
    assert decision.approved is True
    assert decision.reason_code == "FREE_TOOL"
    assert decision.amount == 0.0


@pytest.mark.asyncio
async def test_15_existing_x402_behavior_compatible():
    """Requirement 15: Existing x402 payment service remains compatible."""
    from app.services.payment_service import DEPTH_PRICING_SCHEDULE
    assert DEPTH_PRICING_SCHEDULE["quick"] == 0.005
    assert DEPTH_PRICING_SCHEDULE["standard"] == 0.02
    assert DEPTH_PRICING_SCHEDULE["deep"] == 0.05


@pytest.mark.asyncio
async def test_16_full_agent_manager_pipeline_runs_with_payment_manager():
    """Requirement 16: Research pipeline runs end-to-end with PaymentManager integrated."""
    pm = PaymentManager()
    agent_manager = AgentManager(payment_manager=pm)
    
    job_id = uuid4()
    user_id = uuid4()
    report = await agent_manager.run_pipeline(job_id, user_id, "Multi-agent scaling test")
    
    assert report is not None
    assert report.title is not None
    assert report.content_markdown is not None
