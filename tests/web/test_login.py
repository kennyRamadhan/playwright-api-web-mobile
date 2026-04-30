"""Web UI tests for the login flow."""

import allure

from src.pages.login_page import LoginPage


@allure.epic("Practice Software Testing")
@allure.feature("Login")
class TestLogin:
    @allure.id("WEB-LOGIN-001")
    @allure.title("Login with valid credentials redirects to account page")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_valid_login_redirects_to_account(self, login_page: LoginPage, credentials):
        # Arrange
        await login_page.goto()
        assert await login_page.is_loaded()

        # Act
        await login_page.login(credentials.customer_email, credentials.customer_password)

        # Assert
        await login_page.page.wait_for_url("**/account**", timeout=10_000)
        assert "/account" in login_page.page.url

    @allure.id("WEB-LOGIN-002")
    @allure.title("Login with invalid password shows error message")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_invalid_password_shows_error(self, login_page: LoginPage):
        # Arrange
        await login_page.goto()

        # Act
        await login_page.login("customer@practicesoftwaretesting.com", "wrong-password-xyz")

        # Assert
        await login_page.login_error.wait_for(state="visible", timeout=10_000)
        message = await login_page.error_message()
        assert "invalid" in message.lower() or "password" in message.lower()

    @allure.id("WEB-LOGIN-003")
    @allure.title("Login form prevents submission of empty fields")
    @allure.severity(allure.severity_level.MINOR)
    async def test_empty_submission_is_blocked(self, login_page: LoginPage):
        # Arrange
        await login_page.goto()

        # Act
        await login_page.submit_empty()

        # Assert — Angular form keeps user on the login page when invalid
        assert "/auth/login" in login_page.page.url
        # Email input should carry HTML5 invalid state
        is_invalid = await login_page.email_input.evaluate(
            "el => !el.validity.valid || el.classList.contains('ng-invalid')"
        )
        assert is_invalid
