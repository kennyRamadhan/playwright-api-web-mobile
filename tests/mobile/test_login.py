"""Mobile login flow tests.

Pattern reference: tests/api/test_auth.py and tests/web/test_login.py.
This is the mobile parallel - same AAA + Allure pattern.
"""

from __future__ import annotations

import allure
import pytest
from selenium.common.exceptions import TimeoutException

from src.mobile.screens.login_screen import (
    PASSWORD,
    STANDARD_USER,
    LoginScreen,
)


@allure.epic("Sauce Labs Demo App")
@allure.feature("Authentication")
class TestLogin:
    @pytest.mark.mobile
    @allure.id("MOB-LOGIN-001")
    @allure.title("Valid login with standard user succeeds")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_valid_login_succeeds(self, login_screen: LoginScreen) -> None:
        # Arrange
        login_screen.navigate_to_login()

        # Act
        login_screen.login(STANDARD_USER, PASSWORD)

        # Assert - after successful login, the error element should
        # not appear. Probing with a short timeout: presence within
        # 3 seconds indicates failure, absence indicates success.
        try:
            login_screen.find(*login_screen._ERROR_MESSAGE, timeout=3)
            pytest.fail("Error element present after a valid login")
        except TimeoutException:
            pass  # Expected: no error after valid login

    @pytest.mark.mobile
    @allure.id("MOB-LOGIN-002")
    @allure.title("Invalid password shows error message")
    @allure.severity(allure.severity_level.NORMAL)
    def test_invalid_password_shows_error(self, login_screen: LoginScreen) -> None:
        # Arrange
        login_screen.navigate_to_login()

        # Act
        login_screen.login(STANDARD_USER, "wrong-password")

        # Assert
        error = login_screen.get_error_message()
        assert "Username and password do not match" in error or "Provided credentials" in error, (
            f"Unexpected error message: {error!r}"
        )
