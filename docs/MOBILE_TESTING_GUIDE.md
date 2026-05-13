# Mobile Testing Guide

This guide covers running mobile tests locally and the architecture of
the mobile layer. Target audience: junior QA engineers ramping into
the codebase.

## Overview

The mobile layer adds Appium-driven Android tests against the
[Sauce Labs my-demo-app-rn](https://github.com/saucelabs/my-demo-app-rn)
React Native demo. It mirrors the patterns used by the API and Web
layers but with one major difference: it is **sync rather than async**.

## Why mobile tests are sync

The Appium Python Client has no async API. Mobile gestures
(tap, swipe, type) are inherently sequential — there is no concurrency
benefit to be gained from wrapping a sync API in async syntax.

The framework remains async for API and Web because:

- `httpx` supports concurrent HTTP via async clients
- Playwright is async-first
- Parallel test execution benefits from async I/O at the test boundary

"Async where it adds value, sync where it doesn't" is a deliberate
architectural choice — see `ARCHITECTURE.md` for the full rationale.

## Prerequisites

- Node.js 20+ (for the Appium server runtime)
- Java 17+ (Appium server JVM prereq)
- Android Studio with Android SDK
- An Android emulator (API 31 / Android 12 / Pixel 5 profile recommended)
- `ANDROID_HOME` environment variable set
- Python 3.12+ with `uv`

## One-time setup

```bash
# 1. Install Appium globally
npm install -g appium

# 2. Install the Android UiAutomator2 driver
appium driver install uiautomator2

# 3. Create an AVD (Android Virtual Device) via Android Studio
#    or with avdmanager from the command line. Use API 31, Pixel 5.

# 4. Install Python deps
uv sync

# 5. Download the demo APK (~30 MB, cached locally, gitignored)
python scripts/download_apk.py
```

## Running tests locally

Two terminals:

```bash
# Terminal 1: start emulator (if not already running)
emulator -avd <your-avd-name>

# Then start the Appium server (foreground)
appium
```

```bash
# Terminal 2: run mobile tests
uv run pytest tests/mobile -m mobile -v
```

## Architecture

```
src/mobile/
├── __init__.py
├── driver_factory.py          # get_driver(platform) — central choke point
├── base_screen.py             # BaseScreen — element interaction primitives
├── capabilities/
│   ├── android.py             # UiAutomator2 caps + env overrides
│   └── ios.py                 # Stub — raises NotImplementedError (Phase 2.2)
└── screens/
    ├── login_screen.py        # Canonical example — start reading here
    ├── product_list_screen.py
    ├── product_detail_screen.py
    ├── cart_screen.py
    └── checkout_screen.py

tests/mobile/
├── conftest.py                # Sync driver + screen fixtures + forensics
├── test_login.py              # MOB-LOGIN-001, MOB-LOGIN-002
├── test_browse.py             # MOB-BROWSE-001, MOB-BROWSE-002
├── test_cart.py               # MOB-CART-001
└── test_checkout.py           # MOB-CHECKOUT-001

src/utils/mobile_step.py       # Sync @mobile_step decorator (auto-screenshots)
scripts/download_apk.py        # Fetch v1.3.0 APK to apps/ (gitignored)
```

Flow:

```
test_*.py
  -> @pytest.fixture (sync) in tests/mobile/conftest.py
    -> driver fixture
      -> src/mobile/driver_factory.get_driver("android")
        -> Appium server at http://127.0.0.1:4723
          -> emulator-5554
```

## Test ID convention

Mobile tests use `MOB-{FEATURE}-{NUM}`. Examples:

- `MOB-LOGIN-001` — valid login succeeds
- `MOB-LOGIN-002` — invalid password shows error
- `MOB-BROWSE-001` — product list shows multiple items
- `MOB-CART-001` — add to cart increments badge
- `MOB-CHECKOUT-001` — full purchase E2E

See `ALLURE_TEST_IDS.md` for the full convention across all layers.

## Observability

Mobile observability mirrors web observability:

- `@mobile_step` decorator captures a screenshot after each
  decorated screen-object method, producing a visual storyboard in
  the Allure report.
- On test failure, `tests/mobile/conftest.py` attaches:
  - Final screenshot
  - Page source (XML dump of the UI hierarchy)
  - Current Android activity (which screen)
  - Logcat tail (last 200 lines — captures app crashes, native errors)

## iOS roadmap (Phase 2.2)

iOS support is architecturally ready: `src/mobile/capabilities/ios.py`
exists as a stub, and the driver factory already accepts
`platform="ios"`. Actual implementation is deferred to a later PR
because it requires:

- A macOS host (Xcode-only signing toolchain)
- `my-demo-app-ios` .ipa instead of the Android APK
- A separate macOS-runner CI workflow

Screen objects already prefer `AppiumBy.ACCESSIBILITY_ID` locators
where possible, so most should work cross-platform without changes
once iOS lands.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "No connected devices" | Emulator not running, or `adb devices` empty | Start emulator and confirm `adb devices` shows it |
| "App not installed" | `APP_PATH` env mismatch or APK not downloaded | Run `python scripts/download_apk.py` |
| "Element not found" / TimeoutException | App version drift; locator stale | Dump `driver.page_source` and re-verify the accessibility id |
| Appium connection refused | Server not running on `:4723` | Start `appium` in a separate terminal |
| Emulator crash in CI | API 34+ resource starvation on ubuntu-latest | Workflow pinned to API 31; do not bump without testing |

To inspect actual locators against a running app:

```python
# In a paused test or REPL with an active driver:
print(driver.page_source)
# Search for content-desc / resource-id attributes matching your target
```

Or use the standalone Appium Inspector GUI:
<https://github.com/appium/appium-inspector>

## Cross-reference

- `ARCHITECTURE.md` — design decisions, async-vs-sync rationale
- `ALLURE_TEST_IDS.md` — naming convention across all layers
- `docs/PROJECT_STRUCTURE.md` — folder map (whole repo)
- `docs/CONFTEST_GUIDE.md` — fixture hierarchy explanation
- `docs/CI_OVERVIEW.md` — CI pipeline (mobile workflow runs separately)
- Sauce Labs demo app source: <https://github.com/saucelabs/my-demo-app-rn>
