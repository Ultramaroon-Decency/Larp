import logging
import httpx
from typing import Optional, Dict
from research_agent.app.payment.payment_agent import PaymentAgent

logger = logging.getLogger(__name__)


class X402AsyncTransport(httpx.AsyncBaseTransport):
    """
    Custom httpx AsyncBaseTransport wrapper that intercepts HTTP 402 Payment Required responses,
    automatically negotiates and settles x402 micropayments via PaymentAgent, and retries requests.
    """

    def __init__(self, payment_agent: Optional[PaymentAgent] = None, inner_transport: Optional[httpx.AsyncBaseTransport] = None):
        self.payment_agent = payment_agent or PaymentAgent()
        self.inner = inner_transport or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Executes HTTP request. If target returns HTTP 402, settles payment and retries.
        """
        response = await self.inner.handle_async_request(request)

        # Check if response status code indicates x402 payment required
        headers_dict = dict(response.headers)
        if self.payment_agent.is_payment_required(response.status_code, headers_dict):
            logger.info(f"x402 Interceptor caught HTTP 402 for URL: '{request.url}'. Processing autonomous payment...")
            
            resource_url = str(request.url)
            req = self.payment_agent.parse_payment_requirement(
                resource_url=resource_url,
                status_code=response.status_code,
                headers=headers_dict
            )

            # Process autonomous micropayment
            receipt = await self.payment_agent.process_payment(req)

            # Clone request with payment authorization header
            request.headers["Authorization"] = receipt.authorization_header
            logger.info(f"Retrying request to '{resource_url}' with authorization token: {receipt.authorization_header[:30]}...")
            
            # Retry request
            response = await self.inner.handle_async_request(request)

        return response
