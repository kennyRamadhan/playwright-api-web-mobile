"""User API client for Practice Software Testing."""

from typing import Any

from src.api_clients.base_service import BaseService
from src.models.user import User, UserCreate


class UserService(BaseService):
    """User CRUD operations."""

    async def list_users(self) -> list[User]:
        response = await self._request("GET", "/users")
        body = response.json()
        items = body.get("data", body) if isinstance(body, dict) else body
        return [User.model_validate(item) for item in items]

    async def create_user(self, payload: UserCreate) -> User:
        response = await self._request(
            "POST", "/users/register", json=payload, expected_status=(200, 201)
        )
        return User.model_validate(response.json())

    async def get_current_user(self) -> User:
        response = await self._request("GET", "/users/me")
        return User.model_validate(response.json())

    async def update_current_user(self, **fields: Any) -> User:
        response = await self._request("PUT", "/users/me", json=fields, expected_status=(200, 204))
        return User.model_validate(response.json())

    async def delete_user(self, user_id: str | int) -> None:
        await self._request("DELETE", f"/users/{user_id}", expected_status=(200, 204))
