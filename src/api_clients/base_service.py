"""BaseService — foundation class for all REST API clients in this codebase.

Architectural role
------------------
This is the single point through which every HTTP request flows in the
API testing layer. Centralizing here means:

- Allure instrumentation is automatic for every client (see ``_request``)
- Auth-token management is consistent across services
- Error handling (``APIError``) is uniform
- Adding a new client = subclass + define endpoints, no plumbing

When to extend
--------------
For each REST resource family (auth, products, users, orders, ...) create
one subclass. See ``auth_service.py`` for the canonical example.

When NOT to modify
------------------
``_request`` is the contract every subclass depends on. Changing its
signature breaks every client. Add new helpers as new methods; don't
rewrite ``_request`` unless absolutely necessary.

Related files
-------------
- ``src/utils/assertions.py`` — assertion helpers used in tests
- ``tests/api/conftest.py`` — fixtures that instantiate concrete clients
- ``ARCHITECTURE.md`` — high-level design rationale
- ``docs/LEARNING_PATH.md`` — guided reading order for new readers
"""

from __future__ import annotations

import json as _json
import time
from types import TracebackType
from typing import Any

import allure
import httpx
from pydantic import BaseModel

# Keys whose values must never appear in the published Allure report.
# Lower-cased on lookup so the match is case-insensitive ("Authorization",
# "authorization", and "AUTHORIZATION" all hit). The list is small and
# explicit on purpose — adding a regex pass would over-mask innocent
# fields like "user_password_hint" and damage report readability.
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
    """Recursively redact values for sensitive keys in JSON-like structures.

    Why mask before attaching (not after-the-fact filter): Allure
    attachments are written to disk immediately and become part of the
    public Pages report. A leaked token in a published report cannot be
    retroactively scrubbed without rebuilding the entire history.

    The masked sentinel is the literal string ``"***"`` — chosen over
    ``None`` so JSON serialization stays type-stable downstream.

    The function returns a new structure for nested cases; primitive
    values pass through unchanged. Originals are not mutated.
    """
    if isinstance(data, dict):
        return {
            k: ("***" if k.lower() in _SENSITIVE_KEYS else _mask_sensitive(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_mask_sensitive(item) for item in data]
    return data


def _json_dumps(obj: Any) -> str:
    """Serialize an object to a pretty JSON string for Allure attachments.

    Handles Pydantic models via ``model_dump(mode="json")`` so datetimes,
    enums, and other non-JSON-native types are coerced before encoding.
    Falls back to ``str()`` if ``json.dumps`` cannot represent the value
    — better to attach an imperfect representation than to crash the
    reporting path and lose diagnostic information.
    """
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(mode="json")
    try:
        return _json.dumps(obj, indent=2, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(obj)


class APIError(Exception):
    """Raised when an API call returns a status outside its expected set.

    Carries the status code and the parsed (or raw text) body so tests
    can assert on either. See ``test_invalid_password_returns_401`` in
    ``tests/api/test_auth.py`` for the canonical assertion pattern using
    ``pytest.raises(APIError)``.
    """

    def __init__(self, status_code: int, body: Any, message: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message or f"API returned {status_code}: {body}")


class BaseService:
    """Base class for all API service clients.

    Subclasses define resource-specific methods that delegate to
    ``_request``. Auth tokens are managed here, not per subclass, so a
    single ``set_token`` call upgrades every subsequent call from this
    instance to authenticated.

    Usage::

        async with AuthService(base_url=...) as auth:
            result = await auth.login(email, password)
            # auth is now authenticated for follow-on calls

    Inheritance contract
    --------------------
    Subclasses MUST go through ``self._request`` for any HTTP call so
    they inherit Allure instrumentation, error handling, and auth header
    injection. They MAY add their own helper methods, but should not
    bypass ``_request`` with a raw ``httpx`` call.
    """

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        # Trim trailing slash so subclass paths can use unambiguous "/users/login"
        # without producing a double-slash in the final URL.
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)
        self._token: str | None = None

    def set_token(self, token: str) -> None:
        """Promote subsequent requests to authenticated.

        Called automatically by ``AuthService.login`` on success. Tests
        can also call it directly to reuse a token captured earlier.
        """
        self._token = token

    def clear_token(self) -> None:
        """Drop the token. Used by ``logout`` and by negative-auth tests."""
        self._token = None

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def _headers(self) -> dict[str, str]:
        # Built fresh on every call so that ``set_token`` / ``clear_token``
        # are honoured immediately without stale-header caching bugs.
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
        """Perform an HTTP call, instrument it for Allure, and validate status.

        Wrapping every call in an ``allure.step`` block produces a
        recruiter-readable action tree in the report — request body,
        headers (auth-masked), response status/duration/url, and
        response body all attach as step children. See
        ``ARCHITECTURE.md`` (Allure observability layer) for the design
        rationale.

        Pydantic models passed as ``json`` are dumped with
        ``exclude_none=True`` so optional fields don't surface in the
        request unless the caller explicitly set them — this matches
        how the demo backend treats missing vs null fields.

        Raises ``APIError`` if the response status is not in
        ``expected_status``. The failure body is attached to Allure
        BEFORE the raise so the report shows what actually came back.
        """
        # Convert Pydantic request bodies to plain dict once, up-front.
        # ``exclude_none`` matters: Practice Software Testing rejects
        # explicit nulls on optional fields with a 422 instead of
        # treating them as "not provided".
        if isinstance(json, BaseModel):
            json = json.model_dump(mode="json", exclude_none=True)

        with allure.step(f"{method.upper()} {path}"):
            # Pre-flight attachments — capture the request shape BEFORE
            # the network call so a hung request still leaves a trace.
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

            # Headers are logged with Authorization redacted. We log a
            # COPY of the dict, not the live one used for the request,
            # so the actual token is still sent on the wire.
            headers_for_log: dict[str, str] = dict(self._headers)
            if "Authorization" in headers_for_log:
                headers_for_log["Authorization"] = "Bearer ***"
            allure.attach(
                _json_dumps(headers_for_log),
                name="Request headers",
                attachment_type=allure.attachment_type.JSON,
            )

            # ``perf_counter`` (not ``time.time``) for monotonic, high-resolution
            # duration measurement that's immune to wall-clock adjustments.
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

            # Body attachment is best-effort. Some endpoints return
            # 204 No Content or HTML error pages; we attach what we can
            # without crashing the test. Allure shows TEXT vs JSON
            # icons, so the user sees at a glance whether the body was
            # parseable.
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
                # Re-parse the body for the exception payload (we
                # cannot reuse ``body_for_log`` because it might not
                # exist if the body was non-JSON above).
                try:
                    body: Any = response.json()
                except ValueError:
                    body = response.text
                raise APIError(response.status_code, body)

            return response

    async def close(self) -> None:
        """Release the underlying httpx connection pool.

        Always called by the fixture's ``yield``-then-cleanup pattern in
        ``tests/api/conftest.py`` so a long test run doesn't accumulate
        sockets.
        """
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
