"""Web UI tests for the login flow.

Canonical example of a Web test file. Three things to notice:

1. **Tests never touch selectors.** All DOM access is mediated through
   ``LoginPage`` methods (``goto``, ``login``, ``error_message``).
   When the markup changes, only the page object is updated; tests
   stay intact.

2. **Allure decorators mandatory** — same convention as API tests
   (``@allure.id`` + ``@allure.title``). IDs follow the ``WEB-*``
   prefix (see ``ALLURE_TEST_IDS.md``).

3. **AAA structure with comment markers** — same discipline as API
   tests. The Arrange/Act/Assert split is especially valuable in
   end-to-end UI tests where multiple actions can blur together.

Pattern reference for: every other test file in ``tests/web/``.
"""

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
        # ``is_loaded`` waits for the email input — this guards against
        # racing the SPA's hydration. Without it, ``login`` could fire
        # against a half-rendered form and produce confusing failures.
        assert await login_page.is_loaded()

        # Act
        await login_page.login(credentials.customer_email, credentials.customer_password)

        # Assert
        # Wait for the URL change rather than asserting on it
        # immediately — Playwright's auto-wait handles most cases, but
        # navigation after a form submit is one place explicit waits
        # are still warranted.
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
        # Wait for the error to appear (rather than relying on auto-wait)
        # so the timeout is explicit and tunable.
        await login_page.login_error.wait_for(state="visible", timeout=10_000)
        message = await login_page.error_message()
        # Loose match — the demo's error wording has shifted between
        # "invalid email or password" and "incorrect password" over
        # time. Either word being present is sufficient signal.
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
        # Email input should carry HTML5 invalid state. We check both
        # the native ``validity.valid`` and Angular's ``ng-invalid``
        # class because the demo has used both validation strategies
        # at different times — pinning either keeps the test stable.
        is_invalid = await login_page.email_input.evaluate(
            "el => !el.validity.valid || el.classList.contains('ng-invalid')"
        )
        assert is_invalid
