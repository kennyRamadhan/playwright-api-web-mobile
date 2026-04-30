"""ProductListingPage — home / product grid."""

from playwright.async_api import Locator

from src.pages.base_page import BasePage


class ProductListingPage(BasePage):
    URL_PATH = "/"

    @property
    def product_cards(self) -> Locator:
        return self._page.locator("[data-test^='product-']").filter(
            has=self._page.locator("[data-test='product-name']")
        )

    @property
    def search_input(self) -> Locator:
        return self.by_test_id("search-query")

    @property
    def search_submit(self) -> Locator:
        return self.by_test_id("search-submit")

    @property
    def search_reset(self) -> Locator:
        return self.by_test_id("search-reset")

    @property
    def sort_select(self) -> Locator:
        return self.by_test_id("sort")

    @property
    def no_results_message(self) -> Locator:
        return self.by_test_id("no-results")

    @property
    def cart_quantity_badge(self) -> Locator:
        return self.by_test_id("cart-quantity")

    async def is_loaded(self) -> bool:
        await self._page.wait_for_load_state("domcontentloaded")
        return await self.search_input.is_visible()

    async def product_count(self) -> int:
        await self._page.wait_for_load_state("networkidle")
        return await self.product_cards.count()

    async def search(self, query: str) -> None:
        await self.search_input.fill(query)
        await self.search_submit.click()
        await self._page.wait_for_load_state("networkidle")

    async def sort_by(self, value: str) -> None:
        await self.sort_select.select_option(value)
        await self._page.wait_for_load_state("networkidle")

    async def filter_by_category(self, category_label: str) -> None:
        await self._page.get_by_label(category_label).first.check()
        await self._page.wait_for_load_state("networkidle")

    async def open_first_product(self) -> str:
        first = self.product_cards.first
        name = (await first.locator("[data-test='product-name']").text_content()) or ""
        await first.click()
        return name.strip()

    async def cart_quantity(self) -> int:
        text = (await self.cart_quantity_badge.text_content()) or "0"
        try:
            return int(text.strip())
        except ValueError:
            return 0
