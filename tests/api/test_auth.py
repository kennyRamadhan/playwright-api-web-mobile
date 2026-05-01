"""API tests for ``/users/login``, ``/users/refresh``, ``/users/logout``.

Canonical example of an API test file. Three things to notice:

1. **Allure decorators are mandatory.** Every test has ``@allure.id``
   (stable filterable ID) and ``@allure.title`` (human-readable name).
   The ID convention is documented in ``ALLURE_TEST_IDS.md``.

2. **AAA structure with comment markers.** Every test has explicit
   ``# Arrange``, ``# Act``, ``# Assert`` comments. This is consistent
   discipline — non-negotiable on this project — because it makes a
   test's intent legible without reading the implementation.

3. **Assertion helpers vs raw assert.** Tests mix
   ``expect_field`` (Allure-instrumented, diagnostic) with raw
   ``assert`` (terse, for trivial truthiness). Both are appropriate;
   the choice is about whether the assertion's actual-vs-expected diff
   is worth surfacing as a node in the report.

Pattern reference for: every other test file in ``tests/api/``.
"""

import allure
import httpx
import pytest

from src.api_clients.auth_service import AuthService
from src.api_clients.base_service import APIError
from src.api_clients.user_service import UserService
from src.utils.assertions import expect_field


@allure.epic("Practice Software Testing")
@allure.feature("Authentication")
class TestLogin:
    @allure.id("API-AUTH-200-001")
    @allure.title("Valid login returns access token")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_valid_login_returns_token(self, auth_service: AuthService, credentials):
        # Arrange
        email = credentials.admin_email
        password = credentials.admin_password

        # Act
        response = await auth_service.login(email, password)

        # Assert
        # ``expect_field`` wraps each check in an Allure step so the
        # report shows what was verified, not just pass/fail. Raw
        # ``assert`` is used for the token_type comparison because the
        # AssertionError message is already self-explanatory there.
        expect_field(response, "access_token")
        assert response.token_type.lower() == "bearer", (
            f"Expected 'bearer', got {response.token_type!r}"
        )
        expect_field(response, "expires_in")
        assert response.expires_in > 0, f"Expected positive expires_in, got {response.expires_in}"

    @allure.id("API-AUTH-200-002")
    @allure.title("Token refresh returns a new access token")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_refresh_returns_new_token(self, auth_service: AuthService, credentials):
        # Arrange
        original = await auth_service.login(
            credentials.customer_email, credentials.customer_password
        )

        # Act
        refreshed = await auth_service.refresh()

        # Assert
        # The refresh contract: a new access_token is issued, the client
        # has been updated to the new token, and the original token's
        # presence is preserved (the old token may still be valid until
        # expiry — we don't assert about that).
        assert refreshed.access_token
        assert refreshed.expires_in > 0
        assert auth_service.token == refreshed.access_token
        assert original.access_token

    @allure.id("API-AUTH-401-001")
    @allure.title("Login with invalid password returns 401")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_invalid_password_returns_401(self, auth_service: AuthService, credentials):
        # Arrange
        email = credentials.admin_email
        wrong_password = "definitely-wrong-password"

        # Act / Assert
        # ``pytest.raises`` is the idiomatic way to verify that
        # APIError is raised. We also check the exception's status_code
        # attribute so the test fails informatively if the error were
        # raised for a different reason (network, 5xx, etc).
        with pytest.raises(APIError) as exc_info:
            await auth_service.login(email, wrong_password)
        assert exc_info.value.status_code == 401

    @allure.id("API-AUTH-401-002")
    @allure.title("Calling protected endpoint without token returns 401")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_missing_token_returns_401(self, public_user_service: UserService):
        # Arrange — no token set
        # ``public_user_service`` is the unauthenticated variant from
        # tests/api/conftest.py — using it (instead of clearing a token
        # on a different fixture) keeps the test's intent explicit.
        assert public_user_service.token is None

        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await public_user_service.get_current_user()
        assert exc_info.value.status_code == 401

    @allure.id("API-AUTH-401-003")
    @allure.title("Malformed login body returns 401 (Laravel default)")
    @allure.severity(allure.severity_level.MINOR)
    async def test_malformed_body_returns_401(self, credentials):
        # Note: Practice Software Testing's auth controller treats any
        # malformed login payload as Unauthorized rather than 422 —
        # this test pins that contract so future drift is caught. We
        # bypass AuthService here on purpose because the LoginRequest
        # Pydantic model would refuse the malformed body before sending.
        async with httpx.AsyncClient(base_url=credentials.api_base_url, timeout=15) as client:
            # Arrange / Act
            response = await client.post(
                "/users/login",
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"foo": "bar"},
            )

            # Assert
            assert response.status_code == 401
