"""Web UI tests for product search."""

import allure

from src.pages.product_listing_page import ProductListingPage


@allure.epic("Practice Software Testing")
@allure.feature("Search")
class TestSearch:
    @allure.id("WEB-SEARCH-001")
    @allure.title("Search by product name returns matching results")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_search_returns_matches(self, listing_page: ProductListingPage):
        # Arrange
        await listing_page.goto()
        await listing_page.is_loaded()

        # Act
        await listing_page.search("Pliers")

        # Assert
        count = await listing_page.product_count()
        assert count > 0
        names = await listing_page.page.evaluate(
            """() => Array.from(document.querySelectorAll('[data-test=product-name]'))
                  .map(e => e.textContent.toLowerCase())"""
        )
        assert any("plier" in n for n in names)

    @allure.id("WEB-SEARCH-002")
    @allure.title("Search with no matches shows empty-results state")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_search_no_results_shows_empty_state(self, listing_page: ProductListingPage):
        # Arrange
        await listing_page.goto()
        await listing_page.is_loaded()

        # Act
        await listing_page.search("zzzznotarealproductxx")

        # Assert
        count = await listing_page.product_count()
        assert count == 0
