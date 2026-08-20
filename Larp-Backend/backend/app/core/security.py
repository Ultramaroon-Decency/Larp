"""JWT token creation/verification and password hashing utilities."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt


from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import TokenPayload



def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The ``sub`` claim — user's UUID as string.
        expires_delta: Optional custom lifetime.

    Returns:
        Encoded JWT access token string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or settings.access_token_expire_timedelta)

    to_encode = {
        "sub": str(subject),
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str, jti: str | None = None, expires_delta: timedelta | None = None
) -> tuple[str, str]:
    """Create a signed JWT refresh token.

    Args:
        subject: The ``sub`` claim — user's UUID as string.
        jti: Unique JWT ID claim (UUID4 string if not provided).
        expires_delta: Optional custom lifetime.

    Returns:
        Tuple of (encoded JWT refresh token string, jti).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or settings.refresh_token_expire_timedelta)
    token_jti = jti or str(uuid.uuid4())

    to_encode = {
        "sub": str(subject),
        "type": "refresh",
        "jti": token_jti,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    encoded_token = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_token, token_jti


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token.

    Raises:
        AuthenticationError: If the token is expired, malformed, or invalid type.
    """
    settings = get_settings()
    try:
        payload_dict = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        payload = TokenPayload(**payload_dict)
        if payload.type != "access":
            raise AuthenticationError(
                "Invalid token type — access token expected",
                error_code="AUTH_TOKEN_INVALID_TYPE",
            )
        return payload
    except JWTError:
        raise AuthenticationError(
            "Could not validate credentials",
            error_code="AUTH_TOKEN_INVALID",
        )


def decode_refresh_token(token: str) -> TokenPayload:
    """Decode and validate a JWT refresh token.

    Raises:
        AuthenticationError: If the token is expired, malformed, or invalid type.
    """
    settings = get_settings()
    try:
        payload_dict = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        payload = TokenPayload(**payload_dict)
        if payload.type != "refresh":
            raise AuthenticationError(
                "Invalid token type — refresh token expected",
                error_code="AUTH_TOKEN_INVALID_TYPE",
            )
        return payload
    except JWTError:
        raise AuthenticationError(
            "Invalid or expired refresh token",
            error_code="AUTH_REFRESH_TOKEN_INVALID",
        )


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def verify_google_token(credential: str, audience_client_id: str | None = None) -> dict:
    """Verify a Google ID token server-side and return validated claims.

    Validates signature, expiration, issuer, and audience against Google endpoints.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not credential:
        raise AuthenticationError(
            message="Missing Google ID token credential",
            error_code="AUTH_GOOGLE_TOKEN_MISSING",
        )

    try:
        id_info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            audience_client_id if audience_client_id else None,
            clock_skew_in_seconds=10,
        )
    except Exception as exc:
        raise AuthenticationError(
            message=f"Invalid Google ID token: {str(exc)}",
            error_code="AUTH_GOOGLE_TOKEN_INVALID",
        )

    issuer = id_info.get("iss", "")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise AuthenticationError(
            message=f"Invalid token issuer: {issuer}",
            error_code="AUTH_GOOGLE_INVALID_ISSUER",
        )

    google_sub = id_info.get("sub")
    email = id_info.get("email")
    if not google_sub or not email:
        raise AuthenticationError(
            message="Google token missing required identity claims",
            error_code="AUTH_GOOGLE_CLAIMS_MISSING",
        )

    return id_info

