"""BaseService — foundation for all API clients.

Provides authenticated httpx async client, common error handling,
and response parsing. All API service classes extend this base.
"""

from __future__ import annotations

import json as _json
import time
from types import TracebackType
from typing import Any

import allure
import httpx
from pydantic import BaseModel

_SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization",
}


def _mask_sensitive(data: Any) -> Any:
    """Recursively mask sensitive keys in dicts/lists. Leaves other types alone."""
    if isinstance(data, dict):
        return {
            k: ("***" if k.lower() in _SENSITIVE_KEYS else _mask_sensitive(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_mask_sensitive(item) for item in data]
    return data


def _json_dumps(obj: Any) -> str:
    """Serialize to pretty JSON. Handles Pydantic models; falls back to str()."""
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(mode="json")
    try:
        return _json.dumps(obj, indent=2, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(obj)


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

        with allure.step(f"{method.upper()} {path}"):
            if json is not None:
                allure.attach(
                    _json_dumps(_mask_sensitive(json)),
                    name="Request body",
                    attachment_type=allure.attachment_type.JSON,
                )
            if params is not None:
                allure.attach(
                    _json_dumps(params),
                    name="Query params",
                    attachment_type=allure.attachment_type.JSON,
                )

            headers_for_log: dict[str, str] = dict(self._headers)
            if "Authorization" in headers_for_log:
                headers_for_log["Authorization"] = "Bearer ***"
            allure.attach(
                _json_dumps(headers_for_log),
                name="Request headers",
                attachment_type=allure.attachment_type.JSON,
            )

            start = time.perf_counter()
            response = await self._client.request(
                method=method,
                url=path,
                json=json,
                params=params,
                headers=self._headers,
            )
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            allure.attach(
                _json_dumps(
                    {
                        "status": response.status_code,
                        "duration_ms": duration_ms,
                        "url": str(response.url),
                    }
                ),
                name="Response meta",
                attachment_type=allure.attachment_type.JSON,
            )

            try:
                body_for_log: Any = response.json()
                allure.attach(
                    _json_dumps(body_for_log),
                    name="Response body",
                    attachment_type=allure.attachment_type.JSON,
                )
            except ValueError:
                allure.attach(
                    response.text,
                    name="Response body",
                    attachment_type=allure.attachment_type.TEXT,
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
