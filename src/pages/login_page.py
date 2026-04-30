"""LoginPage — sign-in flow for Practice Software Testing."""

from playwright.async_api import Locator

from src.pages.base_page import BasePage


class LoginPage(BasePage):
    URL_PATH = "/auth/login"

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

    async def login(self, email: str, password: str) -> None:
        await self.email_input.fill(email)
        await self.password_input.fill(password)
        await self.login_button.click()

    async def submit_empty(self) -> None:
        await self.login_button.click()

    async def is_loaded(self) -> bool:
        return await self.email_input.is_visible()

    async def error_message(self) -> str:
        return (await self.login_error.text_content()) or ""
