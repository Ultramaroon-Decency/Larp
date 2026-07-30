"""JWT token creation/verification and password hashing utilities."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)
