"""ProductDetailScreen - single-product detail view.

Pattern reference: see login_screen.py.

Locators marked TO-VERIFY: re-check with driver.page_source on first run.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from src.mobile.base_screen import BaseScreen
from src.utils.mobile_step import mobile_step


class ProductDetailScreen(BaseScreen):
    _ADD_TO_CART = (AppiumBy.ACCESSIBILITY_ID, "Add To Cart button")
    # The product detail screen in my-demo-app-rn does not expose a
    # dedicated `product name` testID — the name is rendered inside the
    # `product description` block alongside the description text. Using
    # that as the readable identity is the most stable signal that the
    # detail screen rendered.
    _PRODUCT_NAME = (AppiumBy.ACCESSIBILITY_ID, "product description")
    _PRODUCT_PRICE = (AppiumBy.ACCESSIBILITY_ID, "product price")
    _CART_BADGE = (AppiumBy.ACCESSIBILITY_ID, "cart badge")
    _CART_BADGE_COUNT = (
        AppiumBy.XPATH,
        '//*[@content-desc="cart badge"]//android.widget.TextView',
    )

    @mobile_step("Tap Add To Cart")
    def tap_add_to_cart(self) -> None:
        self.find(*self._ADD_TO_CART).click()

    @mobile_step("Read product name")
    def get_product_name(self) -> str:
        return str(self.find(*self._PRODUCT_NAME).text)

    @mobile_step("Read product price")
    def get_product_price(self) -> str:
        return str(self.find(*self._PRODUCT_PRICE).text)

    @mobile_step("Tap cart badge to open cart")
    def tap_cart_badge(self) -> None:
        self.find(*self._CART_BADGE).click()

    @mobile_step("Read cart badge count")
    def get_cart_badge_count(self) -> int:
        """Read count from TextView inside the cart-badge ViewGroup."""
        elements = self.driver.find_elements(*self._CART_BADGE_COUNT)
        if not elements:
            return 0
        text = elements[0].text.strip()
        try:
            return int(text)
        except ValueError:
            return 0
