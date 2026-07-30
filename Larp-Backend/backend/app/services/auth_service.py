"""Authentication service."""

from app.config import Settings
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service handling authentication logic.

    Orchestrates user registration, login, and token refresh by
    coordinating the user repository with security utilities.
    """

    def __init__(self, user_repo: UserRepository, settings: Settings) -> None:
        self.user_repo = user_repo
        self.settings = settings

    async def register(self, data: RegisterRequest) -> UserRead:
        """Register a new user account."""
        pass

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and return an access token."""
        pass

    async def refresh_token(self, token: str) -> TokenResponse:
        """Issue a fresh token from a valid existing token."""
        pass
