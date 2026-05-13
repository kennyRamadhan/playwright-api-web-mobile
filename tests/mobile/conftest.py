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
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING, Any

import allure
import pytest

from scripts.download_apk import APK_PATH, download_apk
from src.mobile.driver_factory import get_appium_server_url, get_driver
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


# --- APK auto-provisioning (session-scoped, autouse) ----------------


@pytest.fixture(scope="session", autouse=True)
def ensure_apk() -> None:
    """Make sure the demo APK is on disk before any test runs.

    A first-time clone won't have ``apps/Android-MyDemoAppRN.apk``.
    Rather than failing with an opaque "app not installed" error from
    Appium, download it eagerly. The download is a no-op if the file
    is already cached.

    Skip with ``APP_PATH`` env var (e.g. when pointing at a different
    build). When ``APP_PATH`` is set explicitly we assume the caller
    knows what they're doing and don't second-guess.
    """
    if os.environ.get("APP_PATH"):
        return
    if not APK_PATH.exists():
        download_apk()


# --- Appium server lifecycle (session-scoped, auto-managed) ---------


def _appium_is_up(url: str, timeout: float = 1.0) -> bool:
    """Probe the Appium /status endpoint. Returns True on HTTP 200."""
    try:
        with urllib.request.urlopen(f"{url}/status", timeout=timeout) as resp:  # noqa: S310
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


@pytest.fixture(scope="session", autouse=True)
def appium_server() -> Iterator[None]:
    """Ensure an Appium server is reachable for the whole session.

    Behavior:
        1. If a server is already responding at ``APPIUM_SERVER_URL`` (or
           the default http://127.0.0.1:4723), do nothing — caller is
           responsible for its lifecycle. This matches CI, where the
           workflow starts Appium as a separate step.
        2. Otherwise, spawn ``appium`` as a subprocess, wait up to 30s
           for it to bind, and terminate it on session teardown.

    Why session scope:
        Appium server startup costs ~3s. Per-test would dominate runtime
        for the small mobile suite.

    Why autouse:
        Tests should not have to ask for the server explicitly — it's
        infrastructure, not a test dependency.

    Env override:
        Set ``APPIUM_AUTO_SERVER=0`` to disable auto-management entirely
        (e.g. when running against a remote/Sauce-Labs-style endpoint).
    """
    if os.environ.get("APPIUM_AUTO_SERVER", "1") == "0":
        yield
        return

    url = get_appium_server_url()

    if _appium_is_up(url):
        # Already running — caller owns lifecycle.
        yield
        return

    appium_bin = shutil.which("appium")
    if appium_bin is None:
        pytest.skip(
            "Appium server is not running and 'appium' is not on PATH. "
            "Install with `npm install -g appium` or start the server manually."
        )

    log_path = os.environ.get("APPIUM_LOG", "appium.log")
    log_file = open(log_path, "w", encoding="utf-8")  # noqa: SIM115
    proc = subprocess.Popen(  # noqa: S603
        [appium_bin, "--log-level", "info"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            if _appium_is_up(url):
                break
            if proc.poll() is not None:
                log_file.close()
                with open(log_path, encoding="utf-8", errors="replace") as f:
                    tail = f.read()[-2000:]
                pytest.fail(f"Appium server exited early. Log tail:\n{tail}")
            time.sleep(0.5)
        else:
            pytest.fail(f"Appium server did not become ready within 30s at {url}")

        yield
    finally:
        proc.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        if proc.poll() is None:
            proc.kill()
        log_file.close()


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
