"""BaseService — foundation for all API clients.

Provides authenticated httpx async client, common error handling,
and response parsing. All API service classes extend this base.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx
from pydantic import BaseModel


class APIError(Exception):
    """Raised when an API call returns a non-success status code."""

    def __init__(self, status_code: int, body: Any, message: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message or f"API returned {status_code}: {body}")


class BaseService:
    """Base class for all API service clients.

    Subclasses define resource-specific methods (e.g. AuthService.login).
    Authentication tokens are managed at this level via set_token().
    """

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)
        self._token: str | None = None

    def set_token(self, token: str) -> None:
        self._token = token

    def clear_token(self) -> None:
        self._token = None

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | BaseModel | None = None,
        params: dict[str, Any] | None = None,
        expected_status: int | tuple[int, ...] = 200,
    ) -> httpx.Response:
        if isinstance(json, BaseModel):
            json = json.model_dump(mode="json", exclude_none=True)

        response = await self._client.request(
            method=method,
            url=path,
            json=json,
            params=params,
            headers=self._headers,
        )

        expected = (expected_status,) if isinstance(expected_status, int) else expected_status
        if response.status_code not in expected:
            try:
                body: Any = response.json()
            except ValueError:
                body = response.text
            raise APIError(response.status_code, body)

        return response

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> BaseService:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()
