"""CheckoutPage — /checkout steps 2-4 (billing, payment, confirmation).

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

import allure
from playwright.async_api import Locator

from src.pages.base_page import BasePage


class CheckoutPage(BasePage):
    URL_PATH = "/checkout"

    @property
    def address_input(self) -> Locator:
        return self.by_test_id("address")

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
    def postcode_input(self) -> Locator:
        return self.by_test_id("postcode")

    @property
    def proceed_billing(self) -> Locator:
        return self.by_test_id("proceed-3")

    @property
    def payment_method_select(self) -> Locator:
        return self.by_test_id("payment-method")

    @property
    def confirm_button(self) -> Locator:
        return self.by_test_id("finish")

    @property
    def confirmation_message(self) -> Locator:
        return self.by_test_id("payment-success-message")

    @property
    def payment_error(self) -> Locator:
        return self.by_test_id("payment-error")

    @allure.step("Fill billing address ({city}, {country})")
    async def fill_billing(
        self,
        *,
        address: str = "10 Downing Street",
        city: str = "London",
        state: str = "Greater London",
        country: str = "UK",
        postcode: str = "SW1A 2AA",
    ) -> None:
        await self.address_input.fill(address)
        await self.city_input.fill(city)
        await self.state_input.fill(state)
        await self.country_input.fill(country)
        await self.postcode_input.fill(postcode)

    @allure.step("Select payment method: {method}")
    async def select_payment(self, method: str = "credit-card") -> None:
        await self.payment_method_select.select_option(method)

    @allure.step("Confirm order")
    async def confirm(self) -> None:
        await self.confirm_button.click()

    @allure.step("Check order is confirmed")
    async def is_confirmed(self) -> bool:
        return await self.confirmation_message.is_visible()
