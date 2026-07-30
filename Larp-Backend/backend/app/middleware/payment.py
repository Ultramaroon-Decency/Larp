"""x402 Payment Middleware for automatic pre-execution billing of premium API endpoints.

Intercepts requests to premium API endpoints (e.g. ``POST /api/v1/research/``),
verifies user budget, processes micropayment before route execution, and returns
HTTP 402 Payment Required if balance is insufficient.
"""

import json
from typing import Any, Dict, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import PaymentRequiredError
from app.core.logging import get_logger
from app.middleware.correlation_id import get_correlation_id

logger = get_logger("payment_middleware")

# Paths that require automatic pre-execution payment
PREMIUM_METHODS_AND_PATHS: Set[tuple[str, str]] = {
    ("POST", "/api/v1/research"),
    ("POST", "/api/v1/research/"),
    ("GET", "/api/v1/research/export/pdf"),
}

# Pricing map per depth parameter (in USD)
DEPTH_PRICING: Dict[str, float] = {
    "quick": 0.005,
    "standard": 0.02,
    "deep": 0.05,
}


class PaymentMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware for automatic pre-execution micropayment verification."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Intercept request, check if path requires payment, verify budget, and process payment."""
        method = request.method
        path = request.url.path

        # Check if request targets a premium endpoint requiring pre-payment
        is_premium_target = any(
            method == req_method and path.startswith(req_path)
            for req_method, req_path in PREMIUM_METHODS_AND_PATHS
        )

        if not is_premium_target:
            return await call_next(request)

        # Retrieve authenticated user from request state (populated by AuthenticationMiddleware)
        user = getattr(request.state, "user", None)
        if not user:
            # If request is not authenticated yet, let AuthenticationMiddleware / Dependencies handle 401
            return await call_next(request)

        user_id_str = user.get("id")
        if not user_id_str:
            return await call_next(request)

        # ── 1. Calculate Required API Execution Cost ──────────────────────
        cost_usd = 0.02  # Default standard depth cost
        try:
            # Attempt to parse depth from JSON request body or query params
            if method == "POST":
                # Duplicate request stream for safe reading
                body_bytes = await request.body()
                if body_bytes:
                    payload = json.loads(body_bytes)
                    depth = payload.get("depth", "standard")
                    cost_usd = DEPTH_PRICING.get(str(depth).lower(), 0.02)
        except Exception:
            pass

        # ── 2. Automatic Pre-Execution Micropayment ─────────────────────
        logger.info(
            "PaymentMiddleware: Verifying pre-execution payment",
            user_id=user_id_str,
            path=path,
            cost_usd=cost_usd,
        )

        try:
            from uuid import UUID
            from app.database import get_async_session
            from app.repositories.payment_repository import PaymentRepository
            from app.services.payment_service import PaymentService

            # Obtain session and service instance
            async for session in get_async_session():
                payment_repo = PaymentRepository(session)
                payment_service = PaymentService(payment_repo)

                # Verify user budget (raises PaymentRequiredError if insufficient)
                user_id = UUID(user_id_str)
                await payment_service.verify_user_budget(user_id, cost_usd)

                # Process pre-execution payment
                amount_cents = int(cost_usd * 100)
                payment_result = await payment_service.process_payment_with_retries(
                    user_id=user_id, amount_cents=amount_cents
                )

                # Store payment reference in request state
                request.state.payment_id = payment_result.get("id")
                request.state.cost_usd = cost_usd
                break

        except PaymentRequiredError as exc:
            logger.warning(
                "PaymentMiddleware: Intercepted request — HTTP 402 Payment Required",
                user_id=user_id_str,
                path=path,
                error=exc.message,
            )
            correlation_id = get_correlation_id()
            return JSONResponse(
                status_code=402,
                content={
                    "success": False,
                    "message": exc.message,
                    "error_code": "PAYMENT_REQUIRED",
                    "errors": exc.errors,
                    "correlation_id": correlation_id,
                    "path": path,
                },
            )

        except Exception as exc:
            logger.warning(
                "PaymentMiddleware: Non-blocking payment verification warning",
                error=str(exc),
            )

        # Proceed to route handler execution
        return await call_next(request)
