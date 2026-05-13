"""Mobile test fixtures + failure forensics layer.

This file follows the same patterns as tests/web/conftest.py but for
the sync Appium layer. Key differences from the web conftest:

1. Fixtures are sync (plain @pytest.fixture, not pytest_asyncio.fixture)
   because Appium Python Client is sync.

2. Per-step screenshots are handled by @mobile_step decorator in screens.
   This conftest adds:
   - Driver lifecycle fixture (creates + tears down Appium driver per test)
   - Failure forensics hook: attaches page source, final screenshot,
     logcat, current activity on test failure

3. The pytest_runtest_makereport hook stamps the report onto the item
   so the driver fixture's teardown can read it and conditionally
   attach forensics. Same pattern as tests/web/conftest.py.

For full conftest hierarchy explanation see docs/CONFTEST_GUIDE.md.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING, Any

import allure
import pytest

from src.mobile.driver_factory import get_driver
from src.mobile.screens.cart_screen import CartScreen
from src.mobile.screens.checkout_screen import CheckoutScreen
from src.mobile.screens.login_screen import LoginScreen
from src.mobile.screens.product_detail_screen import ProductDetailScreen
from src.mobile.screens.product_list_screen import ProductListScreen

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver


# --- Failure report stamp hook ---------------------------------------


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """Stamp the call-phase report onto the item for fixture teardown access."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.rep_call = rep  # type: ignore[attr-defined]


# --- Driver fixture --------------------------------------------------


@pytest.fixture
def driver(request: pytest.FixtureRequest) -> Iterator[WebDriver]:
    """Appium driver, scoped per test.

    Creates a fresh driver (and fresh app state via fullReset=False +
    noReset=False) for each test. Teardown attaches forensics if the
    test failed.

    For long test suites, consider switching to session-scoped driver
    with explicit app reset between tests - trades isolation for speed.
    """
    drv = get_driver(platform="android")
    try:
        yield drv

        rep = getattr(request.node, "rep_call", None)
        if rep is not None and rep.failed:
            _attach_failure_forensics(drv)
    finally:
        drv.quit()


def _attach_failure_forensics(driver: WebDriver) -> None:
    """Capture diagnostic artifacts from a failed test driver state."""
    # Final screenshot (full screen)
    with contextlib.suppress(Exception):
        allure.attach(
            driver.get_screenshot_as_png(),
            name="Final screenshot (failure)",
            attachment_type=allure.attachment_type.PNG,
        )

    # Page source (XML dump of UI hierarchy)
    with contextlib.suppress(Exception):
        allure.attach(
            driver.page_source,
            name="Page source at failure",
            attachment_type=allure.attachment_type.XML,
        )

    # Current activity (Android only - what screen are we on)
    with contextlib.suppress(Exception):
        activity = driver.current_activity
        if activity:
            allure.attach(
                activity,
                name="Current activity",
                attachment_type=allure.attachment_type.TEXT,
            )

    # Logcat (Android system log - captures app crashes, native errors)
    with contextlib.suppress(Exception):
        logs = driver.get_log("logcat")
        if logs:
            allure.attach(
                json.dumps(logs[-200:], indent=2),  # last 200 lines
                name="Logcat (last 200 lines)",
                attachment_type=allure.attachment_type.JSON,
            )


# --- Screen object fixtures ------------------------------------------


@pytest.fixture
def login_screen(driver: WebDriver) -> LoginScreen:
    return LoginScreen(driver)


@pytest.fixture
def product_list_screen(driver: WebDriver) -> ProductListScreen:
    return ProductListScreen(driver)


@pytest.fixture
def product_detail_screen(driver: WebDriver) -> ProductDetailScreen:
    return ProductDetailScreen(driver)


@pytest.fixture
def cart_screen(driver: WebDriver) -> CartScreen:
    return CartScreen(driver)


@pytest.fixture
def checkout_screen(driver: WebDriver) -> CheckoutScreen:
    return CheckoutScreen(driver)
