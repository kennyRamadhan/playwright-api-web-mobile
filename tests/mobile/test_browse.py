"""Mobile product browse tests.

Tests cover: catalog rendering, tap into product detail.
Login is NOT required to browse the catalog in my-demo-app-rn.
"""

from __future__ import annotations

import allure
import pytest

from src.mobile.screens.product_detail_screen import ProductDetailScreen
from src.mobile.screens.product_list_screen import ProductListScreen


@allure.epic("Sauce Labs Demo App")
@allure.feature("Browse")
class TestBrowse:
    @pytest.mark.mobile
    @allure.id("MOB-BROWSE-001")
    @allure.title("Product list shows multiple items")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_product_list_not_empty(self, product_list_screen: ProductListScreen) -> None:
        # Arrange / Act - app opens to catalog by default
        count = product_list_screen.get_product_count()

        # Assert
        assert count > 0, "Expected at least one product, got empty list"

    @pytest.mark.mobile
    @allure.id("MOB-BROWSE-002")
    @allure.title("Tap product opens product detail screen")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tap_product_opens_detail(
        self,
        product_list_screen: ProductListScreen,
        product_detail_screen: ProductDetailScreen,
    ) -> None:
        # Arrange - already on product list
        # Act
        product_list_screen.tap_first_product()

        # Assert - product detail surfaces a name and price
        name = product_detail_screen.get_product_name()
        price = product_detail_screen.get_product_price()
        assert name, "Product name not visible on detail screen"
        assert price, "Product price not visible on detail screen"
