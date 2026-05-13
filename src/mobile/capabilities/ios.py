"""iOS capabilities - stub for Phase 2.2.

This file establishes the platform abstraction. Real iOS implementation
deferred to a future PR (Phase 2.2). iOS testing requires Xcode + a
macOS host, which isn't part of this PR's CI matrix.

When iOS support lands:
- Replace NotImplementedError with real XCUITest capabilities
- Add iOS workflow to .github/workflows/ (macOS runner)
- Download my-demo-app-ios .ipa instead of APK
- iOS bundle ID: com.saucelabs.mydemo.app.ios (note the breaking-change dot)
"""

from __future__ import annotations


def get_ios_capabilities() -> dict[str, str | bool | int]:
    """Build iOS capabilities - not yet implemented."""
    raise NotImplementedError(
        "iOS support is deferred to Phase 2.2. See docs/MOBILE_TESTING_GUIDE.md for the roadmap."
    )
