"""LoginPage — sign-in form for Practice Software Testing.

Canonical example of a page object built on ``BasePage``. Three things
to notice:

1. **Selectors are properties.** Each ``@property`` returns a Playwright
   ``Locator``. Locators are lazy — declaring one does NOT touch the
   DOM. The actual lookup happens when an action (``fill``, ``click``)
   runs against the locator. This means the page class can be
   instantiated before navigation without errors.

2. **Methods are user-action-named.** ``login(email, password)`` says
   what the user does. Tests call this. Tests never touch
   ``email_input.fill(...)`` directly.

3. **Allure steps make the action tree readable.** Each public method
   is wrapped in ``@web_step(...)`` so the report shows
   "Login as X" as a node rather than "click(...)" microsteps.

Pattern reference for: every other page object in ``src/pages/``.
"""

from playwright.async_api import Locator

from src.pages.base_page import BasePage
from src.utils.web_step import web_step


class LoginPage(BasePage):
    """The ``/auth/login`` page.

    Usage::

        async def test_login(login_page, credentials):
            await login_page.goto()
            await login_page.login(credentials.customer_email,
                                   credentials.customer_password)
    """

    URL_PATH = "/auth/login"

    # ------------------------------------------------------------------
    # Selectors (properties — lazy locators, not DOM lookups)
    # ------------------------------------------------------------------

    @property
    def email_input(self) -> Locator:
        return self.by_test_id("email")

    @property
    def password_input(self) -> Locator:
        return self.by_test_id("password")

    @property
    def login_button(self) -> Locator:
        return self.by_test_id("login-submit")

    @property
    def login_error(self) -> Locator:
        return self.by_test_id("login-error")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @web_step("Login as {email}")
    async def login(self, email: str, password: str) -> None:
        """Fill the credentials and submit.

        ``password`` is intentionally NOT included in the Allure step
        name — emails are fine to surface in reports for diagnostic
        value, passwords are not.
        """
        await self.email_input.fill(email)
        await self.password_input.fill(password)
        await self.login_button.click()

    @web_step("Submit empty login form")
    async def submit_empty(self) -> None:
        """Click submit without filling anything.

        Used to test that the Angular form blocks the submission and
        surfaces HTML5 / ng-invalid validation state.
        """
        await self.login_button.click()

    @web_step("Check login page is loaded")
    async def is_loaded(self) -> bool:
        """Override: wait for the email input to be visible.

        More precise than the BasePage default (title check) because
        the SPA may route to /auth/login before the form has rendered.
        """
        await self.email_input.wait_for(state="visible", timeout=10_000)
        return True

    @web_step("Read login error message")
    async def error_message(self) -> str:
        """Return the visible error text, or empty string if absent.

        Returns empty rather than raising so the caller can assert on
        the presence/absence of an error explicitly.
        """
        return (await self.login_error.text_content()) or ""
