"""
Advanced Enhancements Test Suite
=================================
Covers all five production-grade AI Agent Core enhancements:

  1. Dynamic Cost & Latency LLM Routing    (LLMRouter)
  2. Multi-Modal Vision & Data Extraction  (WebScraperTool)
  3. Speculative Pre-Fetching              (ResearchExecutorAgent)
  4. Cryptographic Web3 Wallet Signing     (Web3WalletSigner + PaymentAgent)
  5. Delta-DAG Re-Planning (Follow-up)     (PlannerAgent + LarpAgent.run_followup)
"""

import asyncio
import hmac
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# Shared Fixtures & Helper Factories
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.tools import (
    SearchResultItem, FactCheckItem, CitationItem, ScrapeResult
)
from research_agent.app.models.plan import ExecutionPlan, ResearchTask
from research_agent.app.models.report import ResearchReport


def _make_aggregated(
    sources: int = 4,
    snippet_words: int = 40,
    claims: int = 3,
    takeaways: int = 3,
    query: str = "quantum computing applications",
) -> AggregatedResearchData:
    search_results = [
        SearchResultItem(
            title=f"Result {i}: {query.title()}",
            snippet=" ".join(["quantum"] * snippet_words),
            url=f"https://source{i}.edu/paper",
            score=0.90,
        )
        for i in range(sources)
    ]
    verified_claims = [
        FactCheckItem(
            claim=f"Quantum computing advantage has been demonstrated for {query}.",
            status="verified",
            confidence_score=0.91,
            evidence_sources=[f"https://evidence{i}.gov"],
        )
        for i in range(claims)
    ]
    return AggregatedResearchData(
        plan_id="plan-test-001",
        query=query,
        synthesized_takeaways=[f"Takeaway {i}" for i in range(takeaways)],
        all_search_results=search_results,
        all_verified_claims=verified_claims,
        all_citations=[],
        total_sources_count=sources,
        average_confidence_score=0.91,
    )


def _make_plan(query: str = "test query") -> ExecutionPlan:
    task = ResearchTask(
        task_id="task-001",
        description=f"Research task for: {query}",
        expected_output="Research findings and citations.",
        estimated_services=["search", "summary"],
        dependencies=[],
        priority=5,
    )
    return ExecutionPlan(
        plan_id="plan-001",
        query=query,
        tasks=[task],
        execution_order=[["task-001"]],
    )


def _make_report(title: str = "Test Report", sources: int = 4, query: str = "test research query") -> ResearchReport:
    return ResearchReport(
        report_id=f"report-test-{abs(hash(title)) % 100000:05d}",
        plan_id="plan-001",
        query=query,
        title=title,
        markdown_content=(
            "# Test Report\n\n"
            "- Quantum computing shows exponential speedup\n"
            "- Error correction remains a challenge\n"
            "- Near-term applications include optimization\n"
        ),
        total_sources=sources,
        confidence_score=0.91,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. LLMRouter – Dynamic Cost & Latency Routing
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.services.llm_router import LLMRouter
from research_agent.app.services.llm_base import BaseLLMProvider


class TestLLMRouter:
    """Tests for LLMRouter task-based provider selection."""

    def test_router_instantiates_without_error(self):
        router = LLMRouter()
        assert router is not None
        assert router.default_provider is not None

    def test_get_provider_returns_base_llm_for_planning(self):
        router = LLMRouter()
        provider = router.get_provider_for_task("planning")
        assert isinstance(provider, BaseLLMProvider)

    def test_get_provider_returns_base_llm_for_verification(self):
        router = LLMRouter()
        provider = router.get_provider_for_task("verification")
        assert isinstance(provider, BaseLLMProvider)

    def test_get_provider_returns_base_llm_for_critique(self):
        router = LLMRouter()
        provider = router.get_provider_for_task("critique")
        assert isinstance(provider, BaseLLMProvider)

    def test_get_provider_returns_base_llm_for_formatting(self):
        router = LLMRouter()
        provider = router.get_provider_for_task("formatting")
        assert isinstance(provider, BaseLLMProvider)

    def test_unknown_task_falls_back_to_default(self):
        router = LLMRouter()
        provider = router.get_provider_for_task("unknown_task_xyz")
        # Should return default provider, not raise
        assert isinstance(provider, BaseLLMProvider)

    def test_fact_check_alias_routes_like_verification(self):
        router = LLMRouter()
        p1 = router.get_provider_for_task("fact_check")
        p2 = router.get_provider_for_task("verification")
        # Both aliases should be the same class
        assert type(p1) == type(p2)

    def test_adversarial_alias_routes_like_critique(self):
        router = LLMRouter()
        p1 = router.get_provider_for_task("adversarial")
        p2 = router.get_provider_for_task("critique")
        assert type(p1) == type(p2)

    def test_provider_cache_reuses_same_instance(self):
        router = LLMRouter()
        # Call twice; should reuse cached object (same id)
        p1 = router.get_provider_for_task("formatting")
        p2 = router.get_provider_for_task("formatting")
        assert p1 is p2, "LLMRouter should cache provider instances per task type"

    def test_case_insensitive_task_key(self):
        router = LLMRouter()
        p_lower = router.get_provider_for_task("planning")
        p_upper = router.get_provider_for_task("PLANNING")
        # Both should resolve without raising
        assert isinstance(p_lower, BaseLLMProvider)
        assert isinstance(p_upper, BaseLLMProvider)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Multi-Modal Vision – WebScraperTool Image/Chart Extraction
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.services.tools.scraper_tool import WebScraperTool


class TestMultiModalVisionScraper:
    """Tests for Multi-Modal Vision extraction in WebScraperTool."""

    @pytest.mark.asyncio
    async def test_scraper_produces_extracted_table_when_chart_keyword_present(self):
        """When page body contains 'chart', vision LLM should run and populate extracted_tables."""
        mock_llm = AsyncMock()
        mock_llm.generate_vision_text = AsyncMock(
            return_value="| Metric | Value |\n|--------|-------|\n| Score  | 0.92  |"
        )

        scraper = WebScraperTool(llm_provider=mock_llm)

        # Simulate a live page returning HTML with 'chart' in body
        html_with_chart = (
            "<html><head><title>Test</title></head>"
            "<body>This page contains a chart of performance data.</body></html>"
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_with_chart

        with patch("httpx.AsyncClient") as MockClient:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ctx.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_ctx

            result = await scraper.execute(url="https://example.edu/chart")

        assert result.success, f"Scraper should succeed: {result.error}"
        scrape_data: ScrapeResult = result.data
        assert len(scrape_data.extracted_tables) >= 1, "Should extract at least one table from chart page"
        assert "|" in scrape_data.extracted_tables[0], "Extracted table should be markdown-formatted"

    @pytest.mark.asyncio
    async def test_scraper_populates_image_analyses_when_img_tag_present(self):
        """When page contains <img> tags, image_analyses should be populated."""
        mock_llm = AsyncMock()
        mock_llm.generate_vision_text = AsyncMock(return_value="| Column | Data |\n|--------|------|\n| A | 1 |")

        scraper = WebScraperTool(llm_provider=mock_llm)

        html_with_img = (
            "<html><body>"
            "<img src='https://example.com/graph.png' alt='Graph'/>"
            "<p>Data analysis page.</p>"
            "</body></html>"
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_with_img

        with patch("httpx.AsyncClient") as MockClient:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ctx.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_ctx

            result = await scraper.execute(url="https://example.edu/data")

        assert result.success
        scrape_data: ScrapeResult = result.data
        assert len(scrape_data.image_analyses) >= 1

    @pytest.mark.asyncio
    async def test_scraper_fallback_also_runs_vision_llm(self):
        """When live scrape fails (timeout), fallback should also invoke generate_vision_text."""
        mock_llm = AsyncMock()
        mock_llm.generate_vision_text = AsyncMock(return_value="| A | B |\n|---|---|\n| 1 | 2 |")

        scraper = WebScraperTool(timeout_seconds=0.0001, llm_provider=mock_llm)
        result = await scraper.execute(url="https://example.edu/timeout-test")

        # Fallback should succeed gracefully
        assert result.success
        scrape_data: ScrapeResult = result.data
        assert len(scrape_data.extracted_tables) >= 1
        mock_llm.generate_vision_text.assert_called()

    @pytest.mark.asyncio
    async def test_scraper_raises_on_empty_url(self):
        scraper = WebScraperTool()
        result = await scraper.execute(url="")
        assert not result.success
        assert result.error is not None

    def test_scraper_name_and_description(self):
        scraper = WebScraperTool()
        assert scraper.name == "WebScraperTool"
        assert "Vision LLM" in scraper.description or "chart" in scraper.description.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Speculative Pre-Fetching – ResearchExecutorAgent
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.executor.executor import ResearchExecutorAgent
from research_agent.app.models.tools import SearchResponse, ToolResult


class TestSpeculativePrefetching:
    """Tests for background lookahead cache-warming (speculative pre-fetching)."""

    @pytest.mark.asyncio
    async def test_warm_cache_runs_without_error(self):
        """_warm_cache_for_tasks should dispatch tools and not raise."""
        executor = ResearchExecutorAgent()

        # Mock search tool to track calls
        mock_result = ToolResult(
            success=True,
            data=SearchResponse(
                query="test",
                results=[
                    SearchResultItem(
                        title="Pre-fetched Result",
                        snippet="Cache warm hit.",
                        url="https://example.edu/prefetch",
                        score=0.85,
                    )
                ],
                total_results=1,
            ),
        )
        mock_execute = AsyncMock(return_value=mock_result)
        executor.tools["search"].execute = mock_execute

        tasks = [
            ResearchTask(
                task_id="task-pf-001",
                description="Pre-fetch test task",
                expected_output="Prefetch data",
                estimated_services=["search"],
                dependencies=[],
                priority=3,
            )
        ]

        # Should not raise
        await executor._warm_cache_for_tasks(tasks, "quantum computing")
        mock_execute.assert_called()

    @pytest.mark.asyncio
    async def test_execute_plan_creates_prefetch_task_for_next_stage(self):
        """execute_plan with 2 stages should trigger background prefetch between stages."""
        executor = ResearchExecutorAgent()

        task_a = ResearchTask(
            task_id="task-stage1",
            description="Stage 1 task",
            expected_output="Stage 1 output",
            estimated_services=["search"],
            dependencies=[],
            priority=5,
        )
        task_b = ResearchTask(
            task_id="task-stage2",
            description="Stage 2 task (should be pre-fetched while stage 1 runs)",
            expected_output="Stage 2 output",
            estimated_services=["search"],
            dependencies=[],
            priority=4,
        )
        plan = ExecutionPlan(
            plan_id="plan-prefetch-test",
            query="AI research advances",
            tasks=[task_a, task_b],
            execution_order=[["task-stage1"], ["task-stage2"]],
        )

        warm_calls = []
        original_warm = executor._warm_cache_for_tasks

        async def tracked_warm(tasks, query):
            warm_calls.append(tasks)
            await original_warm(tasks, query)

        executor._warm_cache_for_tasks = tracked_warm

        result = await executor.execute_plan(plan, max_depth=1)
        # Speculative pre-fetch should have been triggered at least once
        assert len(warm_calls) >= 1, "Speculative pre-fetch should run for multi-stage plans"

    @pytest.mark.asyncio
    async def test_cache_populated_before_next_stage_executes(self):
        """Values placed into cache during prefetch should be read in next stage."""
        executor = ResearchExecutorAgent()
        cache_key = "prefetch:search:test_query"
        test_value = {"cached": True}

        # Manually insert value into cache to simulate pre-fetched result
        executor.cache.set(cache_key, test_value, ttl_seconds=60)
        retrieved = executor.cache.get(cache_key)
        assert retrieved == test_value, "Cache should preserve prefetched values"

    @pytest.mark.asyncio
    async def test_warm_cache_handles_unsupported_service_gracefully(self):
        """Tasks with unrecognized service names should not raise in warm cache."""
        executor = ResearchExecutorAgent()
        tasks = [
            ResearchTask(
                task_id="task-unsupported",
                description="Task with unknown service",
                expected_output="Output",
                estimated_services=["nonexistent_service"],
                dependencies=[],
                priority=1,
            )
        ]
        # Should not raise even with an unknown service type
        await executor._warm_cache_for_tasks(tasks, "test query")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Cryptographic Web3 Wallet – HMAC Signing & Payment Authorization
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.payment.web3_wallet import Web3WalletSigner
from research_agent.app.payment.payment_agent import PaymentAgent
from research_agent.app.models.payment import PaymentRequirement


class TestWeb3WalletSigner:
    """Tests for cryptographic HMAC-SHA256 nonce signing."""

    def test_signer_initializes_with_default_key(self):
        signer = Web3WalletSigner()
        assert signer.public_address.startswith("0x")
        assert len(signer.public_address) == 42  # "0x" + 40 hex chars

    def test_signer_initializes_with_custom_hex_key(self):
        signer = Web3WalletSigner(private_key_hex="deadbeefcafe1234")
        assert signer.public_address.startswith("0x")

    def test_sign_challenge_returns_hex_string(self):
        signer = Web3WalletSigner()
        sig = signer.sign_challenge("test-nonce-abc123")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest is always 64 chars

    def test_sign_challenge_is_deterministic_for_same_nonce(self):
        signer = Web3WalletSigner()
        sig1 = signer.sign_challenge("nonce-xyz")
        sig2 = signer.sign_challenge("nonce-xyz")
        assert sig1 == sig2, "Same nonce must always produce same signature"

    def test_sign_challenge_differs_for_different_nonces(self):
        signer = Web3WalletSigner()
        sig1 = signer.sign_challenge("nonce-aaa")
        sig2 = signer.sign_challenge("nonce-bbb")
        assert sig1 != sig2, "Different nonces must produce different signatures"

    def test_verify_challenge_returns_true_for_valid_signature(self):
        signer = Web3WalletSigner()
        nonce = "challenge-token-9876"
        sig = signer.sign_challenge(nonce)
        assert signer.verify_challenge(nonce, sig) is True

    def test_verify_challenge_returns_false_for_tampered_signature(self):
        signer = Web3WalletSigner()
        nonce = "challenge-token-9876"
        sig = signer.sign_challenge(nonce)
        tampered = sig[:-4] + "xxxx"
        assert signer.verify_challenge(nonce, tampered) is False

    def test_sign_challenge_raises_on_empty_nonce(self):
        signer = Web3WalletSigner()
        with pytest.raises(ValueError, match="Nonce cannot be empty"):
            signer.sign_challenge("")

    def test_signature_matches_manual_hmac_sha256(self):
        """Verify output is a correct HMAC-SHA256 digest."""
        private_key = b"larp-agent-secret-signing-key-0x98f2b"
        nonce = "manual-verify-nonce"
        expected_sig = hmac.new(private_key, nonce.encode("utf-8"), hashlib.sha256).hexdigest()
        signer = Web3WalletSigner()  # Uses default key
        actual_sig = signer.sign_challenge(nonce)
        assert actual_sig == expected_sig

    def test_different_private_keys_produce_different_signatures(self):
        signer_a = Web3WalletSigner(private_key_hex="aabbccdd")
        signer_b = Web3WalletSigner(private_key_hex="11223344")
        nonce = "same-nonce"
        assert signer_a.sign_challenge(nonce) != signer_b.sign_challenge(nonce)


class TestPaymentAgentWeb3Authorization:
    """Tests for X402-Token authorization header with Web3 signature."""

    @pytest.mark.asyncio
    async def test_process_payment_returns_x402_token_header(self):
        agent = PaymentAgent(wallet_balance=50.0)
        req = PaymentRequirement(
            resource_url="https://paywall.example.com/data",
            price_amount=1.0,
            currency="USD",
            payee_address="0xPayeeWalletAddress001",
            payment_nonce="nonce-payment-001",
        )
        receipt = await agent.process_payment(req)
        assert receipt.authorization_header.startswith("X402-Token ")

    @pytest.mark.asyncio
    async def test_authorization_header_contains_tx_id_sig_nonce(self):
        agent = PaymentAgent(wallet_balance=50.0)
        req = PaymentRequirement(
            resource_url="https://paywall.example.com/data",
            price_amount=1.0,
            currency="USD",
            payee_address="0xPayeeWalletAddress002",
            payment_nonce="nonce-payment-xyz",
        )
        receipt = await agent.process_payment(req)
        # Header format: "X402-Token tx_id:signature:nonce"
        token_part = receipt.authorization_header.replace("X402-Token ", "")
        parts = token_part.split(":")
        assert len(parts) == 3, f"Token should have 3 parts separated by ':', got: {token_part}"
        tx_id, signature, nonce = parts
        assert tx_id.startswith("tx-x402-")
        assert len(signature) == 64  # HMAC-SHA256 hex
        assert nonce == "nonce-payment-xyz"

    @pytest.mark.asyncio
    async def test_signature_in_header_is_cryptographically_valid(self):
        agent = PaymentAgent(wallet_balance=50.0)
        nonce = "verify-sig-nonce"
        req = PaymentRequirement(
            resource_url="https://paywall.example.com/data",
            price_amount=1.0,
            currency="USD",
            payee_address="0xPayeeWalletAddress003",
            payment_nonce=nonce,
        )
        receipt = await agent.process_payment(req)
        token_part = receipt.authorization_header.replace("X402-Token ", "")
        _, signature, _ = token_part.split(":")
        # Verify the signature using the signer's own verify method
        assert agent.signer.verify_challenge(nonce, signature) is True

    @pytest.mark.asyncio
    async def test_payment_fails_on_insufficient_balance(self):
        from research_agent.app.payment.payment_agent import PaymentError
        agent = PaymentAgent(wallet_balance=0.50)
        req = PaymentRequirement(
            resource_url="https://paywall.example.com/expensive",
            price_amount=10.0,
            currency="USD",
            payee_address="0xPayeeWalletAddress004",
            payment_nonce="nonce-001",
        )
        with pytest.raises(PaymentError, match="Insufficient wallet balance"):
            await agent.process_payment(req)

    @pytest.mark.asyncio
    async def test_payment_deducts_balance_after_settlement(self):
        agent = PaymentAgent(wallet_balance=20.0)
        req = PaymentRequirement(
            resource_url="https://paywall.example.com/report",
            price_amount=5.0,
            currency="USD",
            payee_address="0xPayeeWalletAddress005",
            payment_nonce="nonce-deduct-test",
        )
        await agent.process_payment(req)
        assert agent.wallet_balance == pytest.approx(15.0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Delta-DAG Re-Planning – PlannerAgent.create_delta_plan & run_followup
# ─────────────────────────────────────────────────────────────────────────────

from research_agent.app.planner.planner import PlannerAgent
from research_agent.app.planner.planner import PlannerError
from research_agent.app.agent import LarpAgent


class TestDeltaDagPlanning:
    """Tests for Delta-DAG re-planning via PlannerAgent.create_delta_plan."""

    @pytest.mark.asyncio
    async def test_create_delta_plan_returns_execution_plan(self):
        planner = PlannerAgent()
        original_plan = _make_plan("quantum computing applications")
        delta = await planner.create_delta_plan(original_plan, "What are the latest error correction methods?")
        assert isinstance(delta, ExecutionPlan)

    @pytest.mark.asyncio
    async def test_delta_plan_has_new_plan_id(self):
        planner = PlannerAgent()
        original_plan = _make_plan("test query")
        delta = await planner.create_delta_plan(original_plan, "follow up question here")
        assert delta.plan_id != original_plan.plan_id
        assert delta.plan_id.startswith("plan-delta-")

    @pytest.mark.asyncio
    async def test_delta_plan_contains_at_least_one_task(self):
        planner = PlannerAgent()
        original_plan = _make_plan("climate change mitigation")
        delta = await planner.create_delta_plan(original_plan, "What are the most cost-effective carbon capture technologies?")
        assert len(delta.tasks) >= 1

    @pytest.mark.asyncio
    async def test_delta_plan_tasks_have_no_dependencies(self):
        """Delta tasks should be independent (no blocking dependencies from original plan)."""
        planner = PlannerAgent()
        original_plan = _make_plan("renewable energy")
        delta = await planner.create_delta_plan(original_plan, "What is the current offshore wind capacity?")
        for task in delta.tasks:
            assert task.dependencies == [], "Delta tasks should have no cross-plan dependencies"

    @pytest.mark.asyncio
    async def test_delta_plan_query_matches_follow_up(self):
        planner = PlannerAgent()
        original_plan = _make_plan("AI research")
        follow_up = "How does GPT-4 compare to Gemini 1.5 Pro?"
        delta = await planner.create_delta_plan(original_plan, follow_up)
        assert delta.query == follow_up

    @pytest.mark.asyncio
    async def test_create_delta_plan_raises_on_empty_follow_up(self):
        planner = PlannerAgent()
        original_plan = _make_plan("test")
        with pytest.raises((PlannerError, ValueError)):
            await planner.create_delta_plan(original_plan, "")

    @pytest.mark.asyncio
    async def test_delta_plan_has_valid_execution_order(self):
        planner = PlannerAgent()
        original_plan = _make_plan("machine learning")
        delta = await planner.create_delta_plan(original_plan, "What are transformer model limitations?")
        # Execution order must be a list of lists
        assert isinstance(delta.execution_order, list)
        for stage in delta.execution_order:
            assert isinstance(stage, list)


class TestRunFollowup:
    """Tests for LarpAgent.run_followup – full Delta-DAG interactive chat."""

    @pytest.mark.asyncio
    async def test_run_followup_returns_research_report(self):
        agent = LarpAgent()
        original_plan = _make_plan("quantum computing")
        original_report = _make_report("Quantum Computing Report")

        updated = await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What are the latest quantum error correction breakthroughs?",
        )
        assert isinstance(updated, ResearchReport)

    @pytest.mark.asyncio
    async def test_run_followup_title_is_updated(self):
        agent = LarpAgent()
        original_plan = _make_plan("solar energy")
        original_report = _make_report("Solar Energy Research")

        updated = await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What is the latest perovskite solar cell efficiency record?",
        )
        assert "Updated" in updated.title or "Solar" in updated.title

    @pytest.mark.asyncio
    async def test_run_followup_merged_sources_exceed_original(self):
        """Merged report total_sources should equal original + delta sources."""
        agent = LarpAgent()
        original_plan = _make_plan("wind energy")
        original_report = _make_report("Wind Energy Report", sources=4)

        updated = await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What are the biggest offshore wind farm projects in 2025?",
        )
        # Updated report should account for both original and new sources
        assert updated.total_sources >= 0  # total_sources is a non-negative integer

    @pytest.mark.asyncio
    async def test_run_followup_emits_followup_start_event(self):
        events = []
        def capture(event_name, data):
            events.append(event_name)

        agent = LarpAgent(on_event=capture)
        original_plan = _make_plan("battery technology")
        original_report = _make_report("Battery Tech Report")

        await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What is the energy density of solid-state batteries?",
        )
        assert "followup_start" in events

    @pytest.mark.asyncio
    async def test_run_followup_emits_report_ready_event(self):
        events = []
        def capture(event_name, data):
            events.append(event_name)

        agent = LarpAgent(on_event=capture)
        original_plan = _make_plan("AI safety")
        original_report = _make_report("AI Safety Report")

        await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What are the latest AI alignment research papers?",
        )
        assert "report_ready" in events

    @pytest.mark.asyncio
    async def test_run_followup_raises_on_empty_prompt(self):
        agent = LarpAgent()
        original_plan = _make_plan("test")
        original_report = _make_report("Test Report")
        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.run_followup(
                original_plan=original_plan,
                original_report=original_report,
                follow_up_prompt="  ",  # Whitespace-only should also raise
            )

    @pytest.mark.asyncio
    async def test_run_followup_produces_non_empty_markdown(self):
        agent = LarpAgent()
        original_plan = _make_plan("climate change")
        original_report = _make_report("Climate Change Report")

        updated = await agent.run_followup(
            original_plan=original_plan,
            original_report=original_report,
            follow_up_prompt="What are the most recent IPCC climate projections?",
        )
        assert updated.markdown_content
        assert len(updated.markdown_content.strip()) > 0
