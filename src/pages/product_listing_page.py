"""ProductListingPage — home / product grid with search, sort, filter.

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

import allure
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

    @allure.step("Check product listing page is loaded")
    async def is_loaded(self) -> bool:
        await self._page.wait_for_load_state("domcontentloaded")
        await self.search_input.wait_for(state="visible", timeout=10_000)
        return True

    @allure.step("Read product count")
    async def product_count(self) -> int:
        await self._page.wait_for_load_state("networkidle")
        return await self.product_cards.count()

    @allure.step("Search for {query}")
    async def search(self, query: str) -> None:
        await self.search_input.fill(query)
        await self.search_submit.click()
        await self._page.wait_for_load_state("networkidle")

    @allure.step("Sort by {value}")
    async def sort_by(self, value: str) -> None:
        await self.sort_select.select_option(value)
        await self._page.wait_for_load_state("networkidle")

    @allure.step("Filter by category {category_label}")
    async def filter_by_category(self, category_label: str) -> None:
        await self._page.get_by_label(category_label).first.check()
        await self._page.wait_for_load_state("networkidle")

    @allure.step("Open first product")
    async def open_first_product(self) -> str:
        first = self.product_cards.first
        name = (await first.locator("[data-test='product-name']").text_content()) or ""
        await first.click()
        return name.strip()

    @allure.step("Read cart quantity badge")
    async def cart_quantity(self) -> int:
        text = (await self.cart_quantity_badge.text_content()) or "0"
        try:
            return int(text.strip())
        except ValueError:
            return 0
