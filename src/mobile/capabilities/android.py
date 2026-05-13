"""Android capabilities for Appium with UiAutomator2 driver.

These capabilities target a local Android emulator. CI uses the same
capabilities against the emulator spun up by reactivecircus/android-emulator-runner.

Override via environment variables for device flexibility.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_android_capabilities() -> dict[str, str | bool | int]:
    """Build Android capabilities dict for Appium.

    Environment overrides:
        APP_PATH       - path to APK (default: apps/Android-MyDemoAppRN.apk)
        DEVICE_NAME    - emulator/device identifier (default: emulator-5554)
        PLATFORM_VERSION - Android version (default: 12 - matches API 31)
        APPIUM_NEW_COMMAND_TIMEOUT - seconds before driver auto-closes (default: 300)
    """
    apk_path = os.environ.get(
        "APP_PATH",
        str(Path(__file__).parent.parent.parent.parent / "apps" / "Android-MyDemoAppRN.apk"),
    )

    return {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": os.environ.get("DEVICE_NAME", "emulator-5554"),
        "appium:platformVersion": os.environ.get("PLATFORM_VERSION", "12"),
        "appium:app": apk_path,
        "appium:appPackage": "com.saucelabs.mydemoapp.rn",
        "appium:appActivity": "com.saucelabs.mydemoapp.rn.MainActivity",
        "appium:newCommandTimeout": int(os.environ.get("APPIUM_NEW_COMMAND_TIMEOUT", "300")),
        "appium:noReset": False,
        "appium:fullReset": False,
        "appium:autoGrantPermissions": True,
    }
