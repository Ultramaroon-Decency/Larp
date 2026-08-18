import pytest
from research_agent.app.payment import PaymentAgent, PaymentError, PaymentRequirement, PaymentReceipt


def test_payment_required_detection():
    agent = PaymentAgent()

    assert agent.is_payment_required(402) is True
    assert agent.is_payment_required(200) is False
    assert agent.is_payment_required(200, headers={"X-402-Payment-Required": "true"}) is True
    assert agent.is_payment_required(200, headers={"WWW-Authenticate": "x402 realm='search_api'"}) is True


def test_parse_payment_requirement():
    agent = PaymentAgent()
    req = agent.parse_payment_requirement(
        resource_url="https://api.paid-research.com/v1/search",
        status_code=402,
        headers={"x-402-price": "0.25", "x-402-currency": "USDC", "x-402-nonce": "nonce-12345"}
    )

    assert isinstance(req, PaymentRequirement)
    assert req.price_amount == 0.25
    assert req.currency == "USDC"
    assert req.payment_nonce == "nonce-12345"


@pytest.mark.asyncio
async def test_process_payment_success():
    agent = PaymentAgent(wallet_balance=50.0, auto_approve_limit=5.0)
    req = PaymentRequirement(
        resource_url="https://api.paid-research.com/v1/search",
        price_amount=0.50,
        currency="USD",
        payee_address="0x1234567890abcdef",
        payment_nonce="nonce-99999"
    )

    receipt = await agent.process_payment(req)

    assert isinstance(receipt, PaymentReceipt)
    assert receipt.status == "settled"
    assert receipt.payment_nonce == "nonce-99999"
    assert receipt.authorization_header.startswith("X402-Token")
    assert agent.wallet_balance == 49.50
    assert len(agent.transaction_history) == 1


@pytest.mark.asyncio
async def test_process_payment_insufficient_balance():
    agent = PaymentAgent(wallet_balance=0.10)
    req = PaymentRequirement(
        resource_url="https://api.paid-research.com/v1/search",
        price_amount=1.00,
        currency="USD",
        payee_address="0x1234",
        payment_nonce="nonce-111"
    )

    with pytest.raises(PaymentError, match="Insufficient wallet balance"):
        await agent.process_payment(req)


@pytest.mark.asyncio
async def test_process_payment_exceeds_auto_approve_limit():
    agent = PaymentAgent(wallet_balance=100.0, auto_approve_limit=2.0)
    req = PaymentRequirement(
        resource_url="https://api.paid-research.com/v1/search",
        price_amount=5.00,
        currency="USD",
        payee_address="0x1234",
        payment_nonce="nonce-222"
    )

    with pytest.raises(PaymentError, match="exceeds auto-approval safety limit"):
        await agent.process_payment(req)


@pytest.mark.asyncio
async def test_execute_with_payment_retry_workflow():
    agent = PaymentAgent(wallet_balance=10.0)

    # Mock API function that returns 402 on first attempt, and 200 on retry with auth header
    attempt_counter = {"count": 0}

    async def mock_paid_api(auth_header=None):
        attempt_counter["count"] += 1
        if auth_header is None:
            return {"status_code": 402, "price": 0.15, "nonce": "nonce-abc"}
        else:
            assert auth_header.startswith("X402-Token")
            return {"status_code": 200, "data": "Paid research findings content"}

    result = await agent.execute_with_payment_retry(mock_paid_api, "https://api.paid-research.com/v1/search")

    assert attempt_counter["count"] == 2
    assert result["status_code"] == 200
    assert result["data"] == "Paid research findings content"
