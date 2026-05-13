"""Android capabilities for Appium with UiAutomator2 driver.

Device + platform version are auto-detected via `adb devices -l` and
`adb shell getprop` so the same code runs unchanged against:

- A locally-connected real device (preferred when present)
- A locally-running emulator (fallback)
- A CI-managed emulator (DEVICE_NAME / PLATFORM_VERSION are honored if
  the workflow sets them explicitly)

Auto-detection precedence:
    1. Environment overrides (DEVICE_NAME, PLATFORM_VERSION) — explicit
       wins over auto-detection. CI workflows pin these.
    2. First real device returned by `adb devices -l` (anything whose
       serial does not match the emulator pattern).
    3. First emulator returned by `adb devices -l`.

Real-device priority is intentional: when a developer plugs in a phone
they almost certainly want the test to run on it, not on a background
emulator that happens to also be running.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _adb_devices() -> list[tuple[str, bool]]:
    """Return [(serial, is_emulator), ...] from `adb devices`.

    Skips devices in `unauthorized` or `offline` state. Emulators have
    serials like ``emulator-5554``; physical devices have arbitrary
    alphanumeric serials assigned by the manufacturer.

    Returns an empty list if `adb` is not on PATH or the daemon fails.
    """
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["adb", "devices"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    devices: list[tuple[str, bool]] = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if not line or "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        state = state.strip()
        if state != "device":
            continue
        is_emulator = serial.startswith("emulator-")
        devices.append((serial, is_emulator))
    return devices


def _adb_getprop(serial: str, prop: str) -> str | None:
    """Read an Android system property from a specific device."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["adb", "-s", serial, "shell", "getprop", prop],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value or None


def _pick_device() -> tuple[str | None, str | None]:
    """Pick the best available device + its platform version.

    Returns:
        (serial, platform_version) — either may be None if detection
        could not complete. Caller decides how to surface the error.
    """
    devices = _adb_devices()
    if not devices:
        return None, None

    # Real device preference: physical first, emulators only as fallback.
    devices.sort(key=lambda d: d[1])  # False (real) < True (emulator)
    serial = devices[0][0]
    version = _adb_getprop(serial, "ro.build.version.release")
    return serial, version


def get_android_capabilities() -> dict[str, str | bool | int]:
    """Build Android capabilities dict for Appium.

    Environment overrides (all optional):
        APP_PATH                   - path to APK
                                     (default: apps/Android-MyDemoAppRN.apk)
        DEVICE_NAME                - explicit device/emulator serial
                                     (default: auto-detected via adb)
        PLATFORM_VERSION           - explicit Android version
                                     (default: auto-detected via getprop)
        APPIUM_NEW_COMMAND_TIMEOUT - seconds before driver auto-closes
                                     (default: 300)
    """
    apk_path = os.environ.get(
        "APP_PATH",
        str(Path(__file__).parent.parent.parent.parent / "apps" / "Android-MyDemoAppRN.apk"),
    )

    device_name = os.environ.get("DEVICE_NAME")
    platform_version = os.environ.get("PLATFORM_VERSION")

    # Auto-detect anything not explicitly pinned by env.
    if device_name is None or platform_version is None:
        detected_serial, detected_version = _pick_device()
        if device_name is None:
            device_name = detected_serial
        if platform_version is None:
            platform_version = detected_version

    if not device_name:
        raise RuntimeError(
            "No Android device or emulator detected. Connect a device "
            "(USB debugging enabled) or start an emulator. Verify with "
            "`adb devices`."
        )
    if not platform_version:
        raise RuntimeError(
            f"Detected device {device_name!r} but could not read "
            f"ro.build.version.release via adb. Set PLATFORM_VERSION "
            f"explicitly to override."
        )

    return {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": device_name,
        "appium:platformVersion": platform_version,
        "appium:app": apk_path,
        "appium:appPackage": "com.saucelabs.mydemoapp.rn",
        "appium:appActivity": "com.saucelabs.mydemoapp.rn.MainActivity",
        "appium:newCommandTimeout": int(os.environ.get("APPIUM_NEW_COMMAND_TIMEOUT", "300")),
        "appium:noReset": False,
        "appium:fullReset": False,
        "appium:autoGrantPermissions": True,
    }
