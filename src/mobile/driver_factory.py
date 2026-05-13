"""Appium driver factory - abstracts Android vs iOS driver creation.

This is the single point where the test layer touches Appium's
WebDriver constructor. Tests use the driver via fixtures in
tests/mobile/conftest.py and never call this directly.

Pattern reference:
    The factory pattern mirrors src/api_clients/base_service.py - one
    central choke point for cross-cutting concerns. For mobile, that's
    platform abstraction and server URL configuration. For API, it's
    Allure observability.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from appium import webdriver
from appium.options.android import UiAutomator2Options

from src.mobile.capabilities.android import get_android_capabilities
from src.mobile.capabilities.ios import get_ios_capabilities

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver

Platform = Literal["android", "ios"]


def get_appium_server_url() -> str:
    """Return the Appium server URL, overridable via env var."""
    return os.environ.get("APPIUM_SERVER_URL", "http://127.0.0.1:4723")


def get_driver(platform: Platform = "android") -> WebDriver:
    """Create an Appium driver for the given platform.

    Args:
        platform: "android" (default) or "ios" (raises NotImplementedError)

    Returns:
        Appium WebDriver instance. Caller is responsible for calling
        driver.quit() - typically handled by the pytest fixture teardown.

    Raises:
        NotImplementedError: if platform == "ios" (Phase 2.2).
    """
    if platform == "android":
        caps = get_android_capabilities()
        options = UiAutomator2Options().load_capabilities(caps)
        return webdriver.Remote(get_appium_server_url(), options=options)

    if platform == "ios":
        # Surface the iOS capabilities NotImplementedError so the caller
        # gets a clear signal rather than a generic capability error.
        get_ios_capabilities()
        raise RuntimeError("unreachable")

    raise ValueError(f"Unsupported platform: {platform!r}")
