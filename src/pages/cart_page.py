"""CartPage — /checkout step 1, cart contents view.

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

from playwright.async_api import Locator

from src.pages.base_page import BasePage
from src.utils.web_step import web_step


class CartPage(BasePage):
    URL_PATH = "/checkout"

    @property
    def cart_rows(self) -> Locator:
        return self._page.locator("[data-test^='product-']").filter(
            has=self._page.locator("[data-test='product-quantity']")
        )

    @property
    def proceed_button(self) -> Locator:
        return self.by_test_id("proceed-1")

    @property
    def cart_empty_message(self) -> Locator:
        return self._page.get_by_text("The cart is empty", exact=False)

    @web_step("Check cart page is loaded")
    async def is_loaded(self) -> bool:
        return await self._page.locator("h1").is_visible()

    @web_step("Read cart item count")
    async def item_count(self) -> int:
        return await self.cart_rows.count()

    @web_step("Update row {row_index} quantity to {quantity}")
    async def update_quantity(self, row_index: int, quantity: int) -> None:
        row = self.cart_rows.nth(row_index)
        qty_input = row.locator("[data-test='product-quantity']")
        await qty_input.fill(str(quantity))
        await qty_input.press("Tab")

    @web_step("Remove cart row {row_index}")
    async def remove_item(self, row_index: int) -> None:
        row = self.cart_rows.nth(row_index)
        await row.locator("[data-test='product-remove']").click()

    @web_step("Read cart subtotal")
    async def subtotal(self) -> float:
        text = (await self.by_test_id("cart-total").text_content()) or "0"
        cleaned = text.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @web_step("Proceed to checkout")
    async def proceed_to_checkout(self) -> None:
        await self.proceed_button.click()
