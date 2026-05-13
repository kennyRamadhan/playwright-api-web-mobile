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
    _PRODUCT_NAME = (AppiumBy.ACCESSIBILITY_ID, "product name")
    _PRODUCT_PRICE = (AppiumBy.ACCESSIBILITY_ID, "product price")
    _CART_BADGE = (AppiumBy.ACCESSIBILITY_ID, "cart badge")

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
        elements = self.driver.find_elements(*self._CART_BADGE)
        if not elements:
            return 0
        text = elements[0].text.strip()
        try:
            return int(text)
        except ValueError:
            return 0
