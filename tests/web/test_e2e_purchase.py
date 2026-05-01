"""Web UI tests for cart and end-to-end checkout.

Pattern reference: see ``tests/web/test_login.py`` for a fully commented
example of the Web test conventions used here.
"""

import allure
import pytest

from src.pages.cart_page import CartPage
from src.pages.checkout_page import CheckoutPage
from src.pages.login_page import LoginPage
from src.pages.product_detail_page import ProductDetailPage
from src.pages.product_listing_page import ProductListingPage


async def _add_first_product_to_cart(
    listing_page: ProductListingPage, detail_page: ProductDetailPage
) -> None:
    await listing_page.goto()
    await listing_page.is_loaded()
    await listing_page.open_first_product()
    await detail_page.is_loaded()
    await detail_page.add_to_cart(quantity=1)


@allure.epic("Practice Software Testing")
@allure.feature("Cart")
class TestCart:
    @allure.id("WEB-CART-001")
    @allure.title("Adding a product to the cart updates the cart counter")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_add_product_updates_cart_count(
        self,
        listing_page: ProductListingPage,
        detail_page: ProductDetailPage,
    ):
        # Arrange / Act
        await _add_first_product_to_cart(listing_page, detail_page)

        # Assert — cart badge in nav reflects the new item
        await listing_page.page.wait_for_load_state("networkidle")
        cart_badge = listing_page.page.locator("[data-test='nav-cart']")
        await cart_badge.wait_for(state="visible", timeout=10_000)
        cart_text = (await cart_badge.text_content()) or ""
        assert any(ch.isdigit() for ch in cart_text)

    @pytest.mark.skip(
        reason="Stateful cart traversal across pages requires authenticated "
        "session + API-seeded cart fixture. Tracked for Phase 2."
    )
    @allure.id("WEB-CART-002")
    @allure.title("Removing a product from the cart empties the cart view")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_remove_product_empties_cart(
        self,
        listing_page: ProductListingPage,
        detail_page: ProductDetailPage,
        cart_page: CartPage,
    ):
        # Arrange
        await _add_first_product_to_cart(listing_page, detail_page)
        await cart_page.goto()
        await cart_page.page.wait_for_load_state("networkidle")
        starting = await cart_page.item_count()
        assert starting >= 1

        # Act
        await cart_page.remove_item(0)
        await cart_page.page.wait_for_load_state("networkidle")

        # Assert
        assert await cart_page.item_count() == starting - 1

    @pytest.mark.skip(
        reason="Stateful cart traversal across pages requires authenticated "
        "session + API-seeded cart fixture. Tracked for Phase 2."
    )
    @allure.id("WEB-CART-003")
    @allure.title("Updating quantity recalculates cart subtotal")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_update_quantity_recalculates_subtotal(
        self,
        listing_page: ProductListingPage,
        detail_page: ProductDetailPage,
        cart_page: CartPage,
    ):
        # Arrange
        await _add_first_product_to_cart(listing_page, detail_page)
        await cart_page.goto()
        await cart_page.page.wait_for_load_state("networkidle")
        original_subtotal = await cart_page.subtotal()

        # Act
        await cart_page.update_quantity(0, 3)
        await cart_page.page.wait_for_load_state("networkidle")

        # Assert
        new_subtotal = await cart_page.subtotal()
        assert new_subtotal > original_subtotal


@allure.epic("Practice Software Testing")
@allure.feature("Checkout")
class TestCheckout:
    @pytest.mark.skip(
        reason="Multi-step Angular checkout funnel requires per-step waits and "
        "auth state persistence; deferred to Phase 2 alongside storageState fixtures."
    )
    @allure.id("WEB-CHECKOUT-001")
    @allure.title("Full purchase flow completes with bank-transfer payment")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_full_purchase_flow(
        self,
        listing_page: ProductListingPage,
        detail_page: ProductDetailPage,
        cart_page: CartPage,
        login_page: LoginPage,
        checkout_page: CheckoutPage,
        credentials,
    ):
        # Arrange — seed cart, then sign in
        await _add_first_product_to_cart(listing_page, detail_page)
        await login_page.goto()
        await login_page.login(credentials.customer_email, credentials.customer_password)
        await login_page.page.wait_for_url("**/account**", timeout=10_000)

        # Act — proceed through the checkout funnel
        await cart_page.goto()
        await cart_page.page.wait_for_load_state("networkidle")
        await cart_page.proceed_to_checkout()

        # Step 2: address — auto-prefilled for logged-in customers; advance
        proceed_2 = checkout_page.page.locator("[data-test='proceed-2']")
        await proceed_2.click()

        # Step 3: payment
        proceed_3 = checkout_page.page.locator("[data-test='proceed-3']")
        await proceed_3.click()

        # Step 4: payment method
        await checkout_page.payment_method_select.select_option("bank-transfer")
        await checkout_page.page.locator("[data-test='bank_name']").fill("Test Bank")
        await checkout_page.page.locator("[data-test='account_name']").fill("Kenny Tester")
        await checkout_page.page.locator("[data-test='account_number']").fill("123456")
        await checkout_page.page.locator("[data-test='finish']").click()

        # Assert
        success = checkout_page.page.locator("[data-test='payment-success-message']")
        await success.wait_for(state="visible", timeout=15_000)

    @pytest.mark.skip(
        reason="Depends on WEB-CHECKOUT-001 setup (auth + multi-step funnel). Deferred to Phase 2."
    )
    @allure.id("WEB-CHECKOUT-NEG-001")
    @allure.title("Checkout payment step blocks invalid credit card details")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_checkout_invalid_card_blocks_completion(
        self,
        listing_page: ProductListingPage,
        detail_page: ProductDetailPage,
        cart_page: CartPage,
        login_page: LoginPage,
        checkout_page: CheckoutPage,
        credentials,
    ):
        # Arrange
        await _add_first_product_to_cart(listing_page, detail_page)
        await login_page.goto()
        await login_page.login(credentials.customer_email, credentials.customer_password)
        await login_page.page.wait_for_url("**/account**", timeout=10_000)
        await cart_page.goto()
        await cart_page.page.wait_for_load_state("networkidle")
        await cart_page.proceed_to_checkout()
        await checkout_page.page.locator("[data-test='proceed-2']").click()
        await checkout_page.page.locator("[data-test='proceed-3']").click()

        # Act — credit-card with bad card number
        await checkout_page.payment_method_select.select_option("credit-card")
        await checkout_page.page.locator("[data-test='credit_card_number']").fill("0000")
        await checkout_page.page.locator("[data-test='expiration_date']").fill("13/2099")
        await checkout_page.page.locator("[data-test='cvv']").fill("12")
        await checkout_page.page.locator("[data-test='card_holder_name']").fill("X")
        finish_button = checkout_page.page.locator("[data-test='finish']")

        # Assert — Angular validation keeps the finish button disabled OR
        # surfaces a validation-error class on the inputs.
        is_disabled = await finish_button.is_disabled()
        if not is_disabled:
            invalid_count = await checkout_page.page.locator(".ng-invalid").count()
            assert invalid_count > 0, "expected invalid form indicators when card data is bad"
        else:
            assert is_disabled
