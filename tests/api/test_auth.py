"""API tests for the /users/login, /users/refresh, /users/logout endpoints."""

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
        assert refreshed.access_token
        assert refreshed.expires_in > 0
        assert auth_service.token == refreshed.access_token
        assert original.access_token  # original still issued

    @allure.id("API-AUTH-401-001")
    @allure.title("Login with invalid password returns 401")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_invalid_password_returns_401(self, auth_service: AuthService, credentials):
        # Arrange
        email = credentials.admin_email
        wrong_password = "definitely-wrong-password"

        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await auth_service.login(email, wrong_password)
        assert exc_info.value.status_code == 401

    @allure.id("API-AUTH-401-002")
    @allure.title("Calling protected endpoint without token returns 401")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_missing_token_returns_401(self, public_user_service: UserService):
        # Arrange — no token set
        assert public_user_service.token is None

        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await public_user_service.get_current_user()
        assert exc_info.value.status_code == 401

    @allure.id("API-AUTH-401-003")
    @allure.title("Malformed login body returns 401 (Laravel default)")
    @allure.severity(allure.severity_level.MINOR)
    async def test_malformed_body_returns_401(self, credentials):
        # Note: Practice Software Testing's auth controller treats any malformed
        # login payload as Unauthorized rather than 422 — this test pins that
        # contract so future drift is caught.
        async with httpx.AsyncClient(base_url=credentials.api_base_url, timeout=15) as client:
            # Arrange / Act
            response = await client.post(
                "/users/login",
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"foo": "bar"},
            )

            # Assert
            assert response.status_code == 401
