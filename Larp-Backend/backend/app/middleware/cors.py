"""CORS middleware configuration.

Configures ``CORSMiddleware`` with origins loaded from settings and
exposes custom response headers (``X-Request-ID``, ``X-RateLimit-*``)
so browser-based clients can read them from JavaScript.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def setup_cors(app: FastAPI) -> None:
    """Configure CORS for the application.

    - ``allow_origins`` — loaded from ``CORS_ORIGINS`` in settings.
    - ``allow_credentials`` — ``True`` so cookies / Authorization headers
      are sent on cross-origin requests.
    - ``allow_methods`` — all HTTP methods.
    - ``allow_headers`` — all headers (including ``Authorization``).
    - ``expose_headers`` — explicitly lists custom headers that browsers
      may read from JavaScript (CORS hides them by default).
    """
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ],
    )
