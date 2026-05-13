"""CheckoutScreen - multi-step checkout flow.

Pattern reference: see login_screen.py.

The checkout flow in my-demo-app-rn spans multiple screens:
    Shipping Address -> Payment -> Review Order -> Confirmation

Rather than splitting into 4 screen classes (which adds fixture
ceremony without aiding readability), one ``CheckoutScreen`` walks
the user through all four. Each compound step is a distinct
``@mobile_step``-decorated method so the Allure trace still shows
the flow at sub-screen granularity.

Locators marked TO-VERIFY: re-check with driver.page_source on first
run of each sub-screen. The accessibility IDs below are based on
community-documented testIDs for v1.3.0.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from src.mobile.base_screen import BaseScreen
from src.utils.mobile_step import mobile_step


class CheckoutScreen(BaseScreen):
    # Shipping address sub-screen
    _FULL_NAME = (AppiumBy.ACCESSIBILITY_ID, "Full Name* input field")
    _ADDRESS_LINE_1 = (AppiumBy.ACCESSIBILITY_ID, "Address Line 1* input field")
    _CITY = (AppiumBy.ACCESSIBILITY_ID, "City* input field")
    _ZIP_CODE = (AppiumBy.ACCESSIBILITY_ID, "Zip Code* input field")
    _COUNTRY = (AppiumBy.ACCESSIBILITY_ID, "Country* input field")
    _TO_PAYMENT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "To Payment button")

    # Payment sub-screen
    _PAY_FULL_NAME = (AppiumBy.ACCESSIBILITY_ID, "Full Name* input field")
    _CARD_NUMBER = (AppiumBy.ACCESSIBILITY_ID, "Card Number* input field")
    _EXPIRATION = (AppiumBy.ACCESSIBILITY_ID, "Expiration Date* input field")
    _SECURITY_CODE = (AppiumBy.ACCESSIBILITY_ID, "Security Code* input field")
    _REVIEW_ORDER_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Review Order button")

    # Review + confirmation
    _PLACE_ORDER_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Place Order button")
    # Confirmation page is identified by its screen container content-desc.
    _ORDER_CONFIRMATION = (AppiumBy.ACCESSIBILITY_ID, "checkout complete screen")

    @mobile_step("Fill shipping address for {full_name}")
    def fill_shipping_address(
        self,
        full_name: str,
        address_line_1: str,
        city: str,
        zip_code: str,
        country: str,
    ) -> None:
        self.find(*self._FULL_NAME).send_keys(full_name)
        self.find(*self._ADDRESS_LINE_1).send_keys(address_line_1)
        self.find(*self._CITY).send_keys(city)
        self.find(*self._ZIP_CODE).send_keys(zip_code)
        self.find(*self._COUNTRY).send_keys(country)

    @mobile_step("Tap To Payment")
    def tap_to_payment(self) -> None:
        self.find(*self._TO_PAYMENT_BUTTON).click()

    @mobile_step("Fill payment details for {full_name}")
    def fill_payment_details(
        self,
        full_name: str,
        card_number: str,
        expiration: str,
        security_code: str,
    ) -> None:
        self.find(*self._PAY_FULL_NAME).send_keys(full_name)
        self.find(*self._CARD_NUMBER).send_keys(card_number)
        self.find(*self._EXPIRATION).send_keys(expiration)
        self.find(*self._SECURITY_CODE).send_keys(security_code)

    @mobile_step("Tap Review Order")
    def tap_review_order(self) -> None:
        self.find(*self._REVIEW_ORDER_BUTTON).click()

    @mobile_step("Tap Place Order")
    def tap_place_order(self) -> None:
        self.find(*self._PLACE_ORDER_BUTTON).click()

    @mobile_step("Check order confirmation visible")
    def is_order_confirmed(self) -> bool:
        try:
            self.find(*self._ORDER_CONFIRMATION, timeout=10)
            return True
        except Exception:  # noqa: BLE001
            return False
