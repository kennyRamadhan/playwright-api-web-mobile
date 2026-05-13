"""Download and cache the Sauce Labs my-demo-app-rn APK for mobile tests.

Run locally before first mobile test session:
    python scripts/download_apk.py

In CI, this is invoked as a workflow step with actions/cache to avoid
re-downloading on every run.

The APK is large (~30 MB) and is intentionally NOT committed to git.
This script downloads it on demand from the upstream release URL.

Version is pinned to v1.3.0 because:
- saucelabs/my-demo-app-rn was archived in May 2024; v1.3.0 is the
  final release and won't change.
- Accessibility IDs documented in src/mobile/screens/ were verified
  against this version. A pinned version means our screen locators
  cannot drift due to upstream changes.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

APK_URL = (
    "https://github.com/saucelabs/my-demo-app-rn/releases/download/v1.3.0/Android-MyDemoAppRN.apk"
)
APK_DIR = Path(__file__).parent.parent / "apps"
APK_PATH = APK_DIR / "Android-MyDemoAppRN.apk"


def download_apk(force: bool = False) -> Path:
    """Download the demo APK if not already cached.

    Args:
        force: re-download even if the file exists.

    Returns:
        Path to the downloaded APK.
    """
    APK_DIR.mkdir(parents=True, exist_ok=True)

    if APK_PATH.exists() and not force:
        size_mb = APK_PATH.stat().st_size / 1024 / 1024
        print(f"APK already cached at {APK_PATH} ({size_mb:.1f} MB)")
        return APK_PATH

    print(f"Downloading APK from {APK_URL} ...")
    urllib.request.urlretrieve(APK_URL, APK_PATH)  # noqa: S310
    size_mb = APK_PATH.stat().st_size / 1024 / 1024
    print(f"Downloaded to {APK_PATH} ({size_mb:.1f} MB)")
    return APK_PATH


if __name__ == "__main__":
    force = "--force" in sys.argv
    download_apk(force=force)
