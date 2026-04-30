"""Authentication API client for Practice Software Testing."""

from src.api_clients.base_service import BaseService
from src.models.user import LoginRequest, LoginResponse


class AuthService(BaseService):
    """Authentication operations: login, logout, token refresh."""

    async def login(self, email: str, password: str) -> LoginResponse:
        request = LoginRequest(email=email, password=password)
        response = await self._request("POST", "/users/login", json=request)
        result = LoginResponse.model_validate(response.json())
        self.set_token(result.access_token)
        return result

    async def logout(self) -> None:
        await self._request("GET", "/users/logout", expected_status=(200, 204))
        self.clear_token()

    async def refresh(self) -> LoginResponse:
        response = await self._request("GET", "/users/refresh")
        result = LoginResponse.model_validate(response.json())
        self.set_token(result.access_token)
        return result
