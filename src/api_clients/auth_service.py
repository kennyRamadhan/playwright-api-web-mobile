"""AuthService — authentication endpoints for Practice Software Testing.

Canonical example of a ``BaseService`` subclass. Three things to notice:

1. The class is a thin wrapper. All HTTP plumbing lives in
   ``BaseService._request`` — this file only declares which endpoints
   exist and what shape they return.

2. Request bodies are Pydantic models (``LoginRequest``), not raw dicts.
   This guarantees client-side validation before the request even leaves
   the test process and gives editor autocomplete for callers.

3. Responses are validated through Pydantic (``LoginResponse.model_validate``)
   so a contract change on the server (e.g. renamed field) surfaces as a
   clear validation error instead of an ``AttributeError`` deep inside a test.

Pattern reference for: every other client in ``src/api_clients/``.
"""

from src.api_clients.base_service import BaseService
from src.models.user import LoginRequest, LoginResponse


class AuthService(BaseService):
    """Login, logout, and token refresh against ``/users/...`` endpoints.

    Successful ``login`` and ``refresh`` automatically promote this
    instance to authenticated by calling ``set_token`` on itself, so
    follow-up calls to other services that share the same auth state
    are not the responsibility of the test.
    """

    async def login(self, email: str, password: str) -> LoginResponse:
        """POST ``/users/login`` and store the returned access token.

        The token is set on this instance via ``set_token`` so any
        subsequent call (refresh, logout, or any other authenticated
        endpoint reached through this client) carries the bearer header.

        Returns the parsed ``LoginResponse`` so tests can also assert
        on ``access_token``, ``token_type``, and ``expires_in`` values.
        """
        request = LoginRequest(email=email, password=password)
        response = await self._request("POST", "/users/login", json=request)
        result = LoginResponse.model_validate(response.json())
        self.set_token(result.access_token)
        return result

    async def logout(self) -> None:
        """GET ``/users/logout`` and drop the local token.

        The endpoint accepts both 200 and 204 — the demo backend has
        historically alternated between them — so we list both as
        expected. Token is cleared regardless of which we received so
        the client cannot accidentally reuse a logged-out token.
        """
        await self._request("GET", "/users/logout", expected_status=(200, 204))
        self.clear_token()

    async def refresh(self) -> LoginResponse:
        """GET ``/users/refresh`` and rotate the stored token.

        The new token replaces the previous one on this instance. The
        old token may still be valid server-side until expiry; this
        client does not track that — callers who care should login
        again from a fresh ``AuthService``.
        """
        response = await self._request("GET", "/users/refresh")
        result = LoginResponse.model_validate(response.json())
        self.set_token(result.access_token)
        return result
