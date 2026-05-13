"""BaseScreen - foundation class for all mobile screen objects.

Architectural role:
    Mirror of src/pages/base_page.py for the mobile layer. Encapsulates
    common element interaction patterns so screen subclasses focus on
    business actions (login, add_to_cart) rather than WebDriver mechanics.

When to extend:
    For each major screen in the app (Login, Catalog, Cart, etc.) create
    one subclass. See login_screen.py for the canonical example.

Sync by design:
    Appium Python Client is sync. The whole mobile layer is sync - tests,
    fixtures, screens. Do not introduce async here.

Related files:
    - src/utils/mobile_step.py - decorator used by screen public methods
    - tests/mobile/conftest.py - fixtures that instantiate screen objects
    - src/mobile/driver_factory.py - creates the driver passed to screens
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement


DEFAULT_TIMEOUT = 15


class BaseScreen:
    """Base class for all screen objects.

    Subclasses define screen-specific locators and business actions.
    Locators should prefer AppiumBy.ACCESSIBILITY_ID for cross-platform
    portability (iOS Phase 2.2 will share screens where possible).
    """

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def find(
        self,
        by: str,
        value: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> WebElement:
        """Find a single element with explicit wait.

        Args:
            by: locator strategy (AppiumBy.ACCESSIBILITY_ID, etc.)
            value: locator value
            timeout: max seconds to wait for presence (not visibility)
        """
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def find_visible(
        self,
        by: str,
        value: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> WebElement:
        """Find a single element with explicit wait for visibility."""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def by_accessibility_id(self, accessibility_id: str) -> WebElement:
        """Convenience: find by accessibility id (cross-platform preferred)."""
        return self.find(AppiumBy.ACCESSIBILITY_ID, accessibility_id)

    def by_text(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        """Find by visible text using UiAutomator selector (Android)."""
        selector = f'new UiSelector().text("{text}")'
        return self.find(AppiumBy.ANDROID_UIAUTOMATOR, selector, timeout)
