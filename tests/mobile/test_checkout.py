"""Mobile checkout E2E test.

Full purchase flow: login -> add to cart -> checkout -> place order.
Requires authenticated user to complete checkout.
"""

from __future__ import annotations

import allure
import pytest

from src.mobile.screens.cart_screen import CartScreen
from src.mobile.screens.checkout_screen import CheckoutScreen
from src.mobile.screens.login_screen import (
    PASSWORD,
    STANDARD_USER,
    LoginScreen,
)
from src.mobile.screens.product_detail_screen import ProductDetailScreen
from src.mobile.screens.product_list_screen import ProductListScreen


@allure.epic("Sauce Labs Demo App")
@allure.feature("Checkout")
class TestCheckout:
    @pytest.mark.mobile
    @allure.id("MOB-CHECKOUT-001")
    @allure.title("E2E: login, add to cart, checkout, place order")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_purchase_flow(
        self,
        login_screen: LoginScreen,
        product_list_screen: ProductListScreen,
        product_detail_screen: ProductDetailScreen,
        cart_screen: CartScreen,
        checkout_screen: CheckoutScreen,
    ) -> None:
        # Arrange - login first (checkout requires auth)
        login_screen.navigate_to_login()
        login_screen.login(STANDARD_USER, PASSWORD)

        # Act - add product, go to cart, checkout
        product_list_screen.tap_first_product()
        product_detail_screen.tap_add_to_cart()
        product_detail_screen.tap_cart_badge()
        cart_screen.tap_checkout()
        checkout_screen.fill_shipping_address(
            full_name="Kenny Ramadhan",
            address_line_1="123 Test St",
            city="Jakarta",
            zip_code="12345",
            country="Indonesia",
        )
        checkout_screen.tap_to_payment()
        checkout_screen.fill_payment_details(
            full_name="Kenny Ramadhan",
            card_number="4111111111111111",
            expiration="12/30",
            security_code="123",
        )
        checkout_screen.tap_review_order()
        checkout_screen.tap_place_order()

        # Assert
        assert checkout_screen.is_order_confirmed(), "Order confirmation screen not reached"
