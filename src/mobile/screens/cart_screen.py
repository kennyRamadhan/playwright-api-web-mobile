"""CartScreen - shopping cart view.

Pattern reference: see login_screen.py.

Locators marked TO-VERIFY: re-check with driver.page_source on first run.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from src.mobile.base_screen import BaseScreen
from src.utils.mobile_step import mobile_step


class CartScreen(BaseScreen):
    _CHECKOUT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Proceed To Checkout button")
    _CART_ITEM = (AppiumBy.ACCESSIBILITY_ID, "cart store item")
    _REMOVE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "cart remove button")

    @mobile_step("Tap Proceed To Checkout")
    def tap_checkout(self) -> None:
        self.find(*self._CHECKOUT_BUTTON).click()

    @mobile_step("Get cart item count")
    def get_item_count(self) -> int:
        return len(self.driver.find_elements(*self._CART_ITEM))

    @mobile_step("Remove first cart item")
    def remove_first_item(self) -> None:
        self.find(*self._REMOVE_BUTTON).click()
