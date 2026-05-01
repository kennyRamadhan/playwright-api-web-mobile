"""RegisterPage — /auth/register signup form.

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

import allure
from playwright.async_api import Locator

from src.models.user import UserCreate
from src.pages.base_page import BasePage


class RegisterPage(BasePage):
    URL_PATH = "/auth/register"

    @property
    def first_name_input(self) -> Locator:
        return self.by_test_id("first-name")

    @property
    def last_name_input(self) -> Locator:
        return self.by_test_id("last-name")

    @property
    def dob_input(self) -> Locator:
        return self.by_test_id("dob")

    @property
    def street_input(self) -> Locator:
        return self.by_test_id("street")

    @property
    def postcode_input(self) -> Locator:
        return self.by_test_id("postal_code")

    @property
    def city_input(self) -> Locator:
        return self.by_test_id("city")

    @property
    def state_input(self) -> Locator:
        return self.by_test_id("state")

    @property
    def country_input(self) -> Locator:
        return self.by_test_id("country")

    @property
    def phone_input(self) -> Locator:
        return self.by_test_id("phone")

    @property
    def email_input(self) -> Locator:
        return self.by_test_id("email")

    @property
    def password_input(self) -> Locator:
        return self.by_test_id("password")

    @property
    def submit_button(self) -> Locator:
        return self.by_test_id("register-submit")

    @property
    def email_error(self) -> Locator:
        return self.by_test_id("register-error")

    @allure.step("Check register page is loaded")
    async def is_loaded(self) -> bool:
        await self.email_input.wait_for(state="visible", timeout=10_000)
        return True

    async def register(self, user: UserCreate) -> None:
        with allure.step(f"Register user {user.email}"):
            await self.first_name_input.fill(user.first_name)
            await self.last_name_input.fill(user.last_name)
            await self.dob_input.fill(user.dob or "1990-01-01")
            # The Angular form expects country first (it triggers postcode lookup).
            await self.country_input.select_option(value=user.country or "AU")
            await self.postcode_input.fill(user.postcode or "12345")
            await self.street_input.fill(user.address or "1 Test Lane")
            await self.city_input.fill(user.city or "Testville")
            await self.state_input.fill(user.state or "Test State")
            await self.phone_input.fill(user.phone or "0400000000")
            await self.email_input.fill(user.email)
            await self.password_input.fill(user.password)
            await self.submit_button.click()
