"""ProductListScreen - product catalog (the app's home screen).

Pattern reference: see login_screen.py for the canonical example.

Locators marked TO-VERIFY: based on community-documented testIDs for
my-demo-app-rn v1.3.0. Re-verify with driver.page_source on first run.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from src.mobile.base_screen import BaseScreen
from src.utils.mobile_step import mobile_step


class ProductListScreen(BaseScreen):
    _PRODUCT_ITEM = (AppiumBy.ACCESSIBILITY_ID, "store item")
    _CART_BADGE = (AppiumBy.ACCESSIBILITY_ID, "cart badge")
    _SORT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "sort button")

    @mobile_step("Get product count on catalog screen")
    def get_product_count(self) -> int:
        elements = self.driver.find_elements(*self._PRODUCT_ITEM)
        return len(elements)

    @mobile_step("Tap first product in catalog")
    def tap_first_product(self) -> None:
        self.find(*self._PRODUCT_ITEM).click()

    @mobile_step("Read cart badge count")
    def get_cart_badge_count(self) -> int:
        """Return the current cart badge number, or 0 if badge not present."""
        elements = self.driver.find_elements(*self._CART_BADGE)
        if not elements:
            return 0
        text = elements[0].text.strip()
        try:
            return int(text)
        except ValueError:
            return 0

    @mobile_step("Open sort modal")
    def open_sort_modal(self) -> None:
        self.find(*self._SORT_BUTTON).click()
