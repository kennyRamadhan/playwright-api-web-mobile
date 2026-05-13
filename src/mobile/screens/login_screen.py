"""LoginScreen - sign-in flow for my-demo-app-rn.

Pattern reference: see this file for full-commented example of the
BaseScreen pattern used in this codebase. Other screens follow this
same pattern.

The my-demo-app-rn login screen is reached via the hamburger menu
-> "Log In" item. Pre-seeded credentials are listed on the login screen
itself for testing convenience.

Locators: accessibility IDs are based on the testID attributes set in
my-demo-app-rn v1.3.0 source. To verify against actual app, run:
    print(driver.page_source)
and inspect content-desc / resource-id attributes.

Marked TO-VERIFY: re-check on first emulator run; community-documented
locators below may need adjustment.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from src.mobile.base_screen import BaseScreen
from src.utils.mobile_step import mobile_step

# Pre-seeded test users surfaced on the login screen
STANDARD_USER = "bob@example.com"
LOCKED_USER = "alice@example.com"
PASSWORD = "10203040"


class LoginScreen(BaseScreen):
    # Locators - TO-VERIFY against actual app on first run.
    _USERNAME_INPUT = (AppiumBy.ACCESSIBILITY_ID, "Username input field")
    _PASSWORD_INPUT = (AppiumBy.ACCESSIBILITY_ID, "Password input field")
    _LOGIN_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Login button")
    _ERROR_MESSAGE = (AppiumBy.ACCESSIBILITY_ID, "generic-error-message")
    _MENU_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "open menu")
    _LOGIN_MENU_ITEM = (AppiumBy.ACCESSIBILITY_ID, "menu item log in")

    @mobile_step("Open hamburger menu and tap Log In")
    def navigate_to_login(self) -> None:
        self.find(*self._MENU_BUTTON).click()
        self.find(*self._LOGIN_MENU_ITEM).click()

    @mobile_step("Enter username {username}")
    def enter_username(self, username: str) -> None:
        elem = self.find(*self._USERNAME_INPUT)
        elem.clear()
        elem.send_keys(username)

    @mobile_step("Enter password")
    def enter_password(self, password: str) -> None:
        elem = self.find(*self._PASSWORD_INPUT)
        elem.clear()
        elem.send_keys(password)

    @mobile_step("Tap Login button")
    def tap_login(self) -> None:
        self.find(*self._LOGIN_BUTTON).click()

    @mobile_step("Login as {username}")
    def login(self, username: str, password: str) -> None:
        """Compound action: enter credentials and submit."""
        self.enter_username(username)
        self.enter_password(password)
        self.tap_login()

    @mobile_step("Read error message")
    def get_error_message(self) -> str:
        return str(self.find(*self._ERROR_MESSAGE).text)
