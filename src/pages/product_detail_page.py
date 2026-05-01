"""ProductDetailPage — single product view (/product/<id>).

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

import allure
from playwright.async_api import Locator

from src.pages.base_page import BasePage


class ProductDetailPage(BasePage):
    @property
    def product_name(self) -> Locator:
        return self.by_test_id("product-name")

    @property
    def product_price(self) -> Locator:
        return self.by_test_id("unit-price")

    @property
    def quantity_input(self) -> Locator:
        return self.by_test_id("quantity")

    @property
    def add_to_cart_button(self) -> Locator:
        return self.by_test_id("add-to-cart")

    @allure.step("Check product detail page is loaded")
    async def is_loaded(self) -> bool:
        return await self.add_to_cart_button.is_visible()

    @allure.step("Add to cart (quantity={quantity})")
    async def add_to_cart(self, quantity: int = 1) -> None:
        if quantity != 1:
            await self.quantity_input.fill(str(quantity))
        await self.add_to_cart_button.click()
        await self._page.wait_for_load_state("networkidle")
