"""Custom exception hierarchy.

Every exception in this module maps to a specific HTTP status code and
carries structured metadata for the error handler:

- ``message`` — human-readable summary shown to the client.
- ``status_code`` — HTTP status code (401, 404, 409, …).
- ``error_code`` — machine-readable string for programmatic handling
  (e.g. ``"AUTH_TOKEN_EXPIRED"``, ``"DB_CONNECTION_FAILED"``).
- ``errors`` — optional list of detail strings (field errors, etc.).

The error handler in ``middleware/error_handler.py`` catches these and
returns a standardized ``ErrorResponse`` JSON envelope.

Exception Hierarchy::

    AppException (base)
    ├── ValidationError        422  Unprocessable Entity
    ├── AuthenticationError    401  Unauthorized
    ├── AuthorizationError     403  Forbidden
    ├── NotFoundError          404  Not Found
    ├── ConflictError          409  Conflict
    ├── RateLimitError         429  Too Many Requests
    ├── DatabaseError          503  Service Unavailable
    │   ├── DatabaseConnectionError
    │   └── DatabaseIntegrityError  409
    └── ExternalServiceError   502  Bad Gateway
"""


class AppException(Exception):
    """Base exception for all application errors.

    Every subclass sets a default ``status_code`` and ``error_code``.
    Route handlers and service methods raise these; the global error
    handler converts them into standardised JSON responses.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        errors: list | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.errors = errors or []
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class PaymentRequiredError(AppException):
    """402 — Payment Required / Insufficient User Budget."""

    def __init__(
        self,
        message: str = "Payment required: Insufficient budget or user balance",
        errors: list | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=402,
            error_code="PAYMENT_REQUIRED",
            errors=errors,
        )


class ValidationError(AppException):
    """422 — Request body / params failed domain validation.

    Usage::

        raise ValidationError(
            "Password must be at least 8 characters",
            errors=["password: String should have at least 8 characters"],
        )
    """

    def __init__(
        self,
        message: str = "Validation failed",
        errors: list | None = None,
        error_code: str = "VALIDATION_ERROR",
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code=error_code,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Authentication / Authorization
# ---------------------------------------------------------------------------

class AuthenticationError(AppException):
    """401 — Missing, invalid, or expired credentials.

    Usage::

        raise AuthenticationError("Token has expired")
        raise AuthenticationError("Invalid email or password",
                                   error_code="AUTH_INVALID_CREDENTIALS")
    """

    def __init__(
        self,
        message: str = "Could not validate credentials",
        errors: list | None = None,
        error_code: str = "AUTH_FAILED",
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            errors=errors,
        )


class AuthorizationError(AppException):
    """403 — Authenticated but not authorized for this action.

    Usage::

        raise AuthorizationError("You do not own this research session")
    """

    def __init__(
        self,
        message: str = "Insufficient permissions",
        errors: list | None = None,
        error_code: str = "FORBIDDEN",
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Resource errors
# ---------------------------------------------------------------------------

class NotFoundError(AppException):
    """404 — Requested resource does not exist.

    Usage::

        raise NotFoundError(f"Research session '{session_id}' not found")
    """

    def __init__(
        self,
        message: str = "Resource not found",
        errors: list | None = None,
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            errors=errors,
        )


class ConflictError(AppException):
    """409 — Action conflicts with current state (duplicate, etc.).

    Usage::

        raise ConflictError("A user with this email already exists")
    """

    def __init__(
        self,
        message: str = "Resource conflict",
        errors: list | None = None,
        error_code: str = "CONFLICT",
    ) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class RateLimitError(AppException):
    """429 — Client has exceeded the request rate limit.

    Usage::

        raise RateLimitError("100 requests per 60 seconds exceeded")
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        errors: list | None = None,
        error_code: str = "RATE_LIMIT_EXCEEDED",
    ) -> None:
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Database errors
# ---------------------------------------------------------------------------

class DatabaseError(AppException):
    """503 — Database operation failed.

    Base class for all database-related exceptions.  Using 503
    (Service Unavailable) because the root cause is an infrastructure
    dependency, not the client's request.

    Usage::

        raise DatabaseError("Failed to execute query")
    """

    def __init__(
        self,
        message: str = "A database error occurred",
        errors: list | None = None,
        error_code: str = "DATABASE_ERROR",
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code=error_code,
            errors=errors,
        )


class DatabaseConnectionError(DatabaseError):
    """503 — Could not connect to the database.

    Usage::

        raise DatabaseConnectionError()
    """

    def __init__(
        self,
        message: str = "Database connection failed",
        errors: list | None = None,
    ) -> None:
        super().__init__(
            message=message,
            errors=errors,
            error_code="DB_CONNECTION_FAILED",
        )


class DatabaseIntegrityError(DatabaseError):
    """409 — Integrity constraint violated (unique, FK, check).

    Uses 409 (Conflict) instead of 503 because this is usually
    caused by the client's data (duplicate email, missing FK, …).

    Usage::

        raise DatabaseIntegrityError("Email already registered")
    """

    def __init__(
        self,
        message: str = "Data integrity constraint violated",
        errors: list | None = None,
    ) -> None:
        super().__init__(
            message=message,
            errors=errors,
            error_code="DB_INTEGRITY_ERROR",
        )
        # Override status to 409 — this is a client-caused conflict
        self.status_code = 409


# ---------------------------------------------------------------------------
# External service errors
# ---------------------------------------------------------------------------

class ExternalServiceError(AppException):
    """502 — An external API or service call failed.

    Usage::

        raise ExternalServiceError("Search API returned 500")
    """

    def __init__(
        self,
        message: str = "External service unavailable",
        errors: list | None = None,
        error_code: str = "EXTERNAL_SERVICE_ERROR",
    ) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code=error_code,
            errors=errors,
        )
