"""Mobile cart flow tests.

Covers: add to cart, cart badge increment.
"""

from __future__ import annotations

import allure
import pytest

from src.mobile.screens.product_detail_screen import ProductDetailScreen
from src.mobile.screens.product_list_screen import ProductListScreen


@allure.epic("Sauce Labs Demo App")
@allure.feature("Cart")
class TestCart:
    @pytest.mark.mobile
    @allure.id("MOB-CART-001")
    @allure.title("Adding product to cart increments cart count")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_to_cart_increments_count(
        self,
        product_list_screen: ProductListScreen,
        product_detail_screen: ProductDetailScreen,
    ) -> None:
        # Arrange
        baseline = product_list_screen.get_cart_badge_count()

        # Act
        product_list_screen.tap_first_product()
        product_detail_screen.tap_add_to_cart()

        # Assert
        new_count = product_detail_screen.get_cart_badge_count()
        assert new_count == baseline + 1, f"Expected cart count {baseline + 1}, got {new_count}"
