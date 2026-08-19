import uuid
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from research_agent.app.models.payment import PaymentRequirement, PaymentReceipt, PaymentTransaction
from research_agent.app.payment.web3_wallet import Web3WalletSigner

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Exception raised when payment processing fails."""
    pass


class PaymentAgent:
    """
    Payment Agent responsible for detecting HTTP 402 Payment Required status,
    processing autonomous x402 micro-payments, generating settlement receipts,
    and handling automatic request retries.

    New in this version:
        - Cryptographic Web3 Signatures: Signs challenge nonces returned by paywalls
          using Ed25519-like keypair HMAC-SHA256 tokens, verifying key ownership.
    """

    def __init__(self, wallet_balance: float = 100.0, auto_approve_limit: float = 10.0, private_key_hex: str = ""):
        self.wallet_balance = wallet_balance
        self.auto_approve_limit = auto_approve_limit
        self.transaction_history: Dict[str, PaymentTransaction] = {}
        # Instantiate cryptographic Web3 signer
        self.signer = Web3WalletSigner(private_key_hex=private_key_hex)

    def is_payment_required(self, status_code: int, headers: Optional[Dict[str, str]] = None) -> bool:
        """
        Determines if an API response requires x402 payment.
        """
        if status_code == 402:
            return True
        if headers:
            normalized_headers = {k.lower(): v for k, v in headers.items()}
            if "x-402-payment-required" in normalized_headers or "www-authenticate" in normalized_headers and "x402" in normalized_headers["www-authenticate"].lower():
                return True
        return False

    def parse_payment_requirement(
        self,
        resource_url: str,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> PaymentRequirement:
        """
        Extracts payment parameters from HTTP 402 response headers or body payload.
        """
        headers = headers or {}
        norm_headers = {k.lower(): v for k, v in headers.items()}
        body = body or {}

        price = float(norm_headers.get("x-402-price", body.get("price", 0.10)))
        currency = norm_headers.get("x-402-currency", body.get("currency", "USD"))
        payee = norm_headers.get("x-402-payee", body.get("payee", "0x0000000000000000000000000000000000000000"))
        nonce = norm_headers.get("x-402-nonce", body.get("nonce", f"nonce-{uuid.uuid4().hex[:8]}"))

        return PaymentRequirement(
            resource_url=resource_url,
            price_amount=price,
            currency=currency,
            payee_address=payee,
            payment_nonce=nonce,
            scheme="x402"
        )

    async def process_payment(self, req: PaymentRequirement) -> PaymentReceipt:
        """
        Autonomous payment settlement processor.
        Validates wallet balance, deducts cost, generates signed receipt.
        """
        logger.info(f"Processing x402 payment for '{req.resource_url}' (${req.price_amount} {req.currency})...")

        if req.price_amount > self.wallet_balance:
            raise PaymentError(f"Insufficient wallet balance. Required: ${req.price_amount}, Available: ${self.wallet_balance}")

        if req.price_amount > self.auto_approve_limit:
            raise PaymentError(f"Payment amount (${req.price_amount}) exceeds auto-approval safety limit (${self.auto_approve_limit}).")

        # Deduct balance
        self.wallet_balance -= req.price_amount
        tx_id = f"tx-x402-{uuid.uuid4().hex[:10]}"

        # Cryptographically sign the server challenge nonce using private key
        signature = self.signer.sign_challenge(req.payment_nonce)

        receipt = PaymentReceipt(
            tx_id=tx_id,
            payment_nonce=req.payment_nonce,
            status="settled",
            # Standardized Web3 x402 Bearer token: tx_id:signature:nonce
            authorization_header=f"X402-Token {tx_id}:{signature}:{req.payment_nonce}"
        )

        # Log transaction record
        tx_record = PaymentTransaction(
            tx_id=tx_id,
            resource_url=req.resource_url,
            amount=req.price_amount,
            currency=req.currency,
            status="settled",
            timestamp=receipt.timestamp
        )
        self.transaction_history[tx_id] = tx_record

        logger.info(f"Payment settled! TxID: {tx_id}. Remaining wallet balance: ${self.wallet_balance:.2f}")
        return receipt

    async def execute_with_payment_retry(
        self,
        request_func: Callable[[Optional[str]], Awaitable[Any]],
        resource_url: str
    ) -> Any:
        """
        Wrapper that executes an HTTP request, catches HTTP 402 payment requirements,
        automatically processes x402 payments, and retries the request with payment receipt attached.
        """
        res = await request_func(None)
        
        # Check if first request yielded a tuple of (status_code, headers, body) or response dict requiring payment
        status_code = getattr(res, "status_code", res.get("status_code", 200) if isinstance(res, dict) else 200)
        headers = getattr(res, "headers", res.get("headers", {}) if isinstance(res, dict) else {})

        if self.is_payment_required(status_code, headers):
            logger.info(f"402 Payment Required detected for '{resource_url}'. Triggering payment workflow.")
            req = self.parse_payment_requirement(
                resource_url=resource_url,
                status_code=status_code,
                headers=headers,
                body=res if isinstance(res, dict) else {}
            )

            receipt = await self.process_payment(req)
            # Retry request passing payment authorization header
            logger.info(f"Retrying request to '{resource_url}' with payment authorization token...")
            return await request_func(receipt.authorization_header)

        return res
