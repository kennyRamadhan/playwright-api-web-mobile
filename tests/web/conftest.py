"""Web-layer fixtures + visual forensics layer.

What belongs here
-----------------
Two concerns share this file:

1. **Page-object fixtures.** Each fixture takes the shared ``page``
   (defined here, overriding the root) and the session-scoped
   ``credentials``, then builds the page object.

2. **Visual forensics.** Per-step screenshots are produced by the
   ``@web_step`` decorator inside page objects (see
   ``src/utils/web_step.py``). This conftest adds the
   *test-scoped* layers:

   - **Playwright tracing** started at context creation, stopped at
     teardown, attached to Allure on failure.
   - **Console + network listeners** registered on the page,
     populating a per-test forensics holder. Attached on failure.
   - **Final state capture** (URL, full-page screenshot, HTML)
     performed in the async ``page`` fixture teardown when the
     test failed.

Why ``page`` and ``context`` are overridden here
------------------------------------------------
The root ``conftest.py`` defines minimal Playwright primitives that
work for both API and web tests. Web tests need extra plumbing
(tracing, listeners) that API tests do not. Overriding the
fixtures at the ``tests/web/`` scope keeps the cost out of the API
suite without forking the root setup.

Why captures happen in fixture teardown, not in the makereport hook
-------------------------------------------------------------------
``pytest_runtest_makereport`` runs in a *synchronous* context. The
Playwright async API (``page.screenshot``, ``page.content``,
``ctx.tracing.stop``) cannot be invoked safely from there because
no event loop is running by the time the hook fires.

The clean fix is to split responsibilities:

- The hook (sync) only stamps the report onto ``item.rep_call``.
- The async ``page`` and ``context`` fixture teardowns inspect that
  flag and run the async captures inside the still-live event loop,
  attaching to Allure as they go.

This avoids the loop.run_until_complete() footgun entirely.

Pattern reference for: any future addition of failure-time
diagnostics that require async I/O.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import allure
import pytest
import pytest_asyncio
from playwright.async_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Request,
)

from src.pages.account_page import AccountPage
from src.pages.cart_page import CartPage
from src.pages.checkout_page import CheckoutPage
from src.pages.login_page import LoginPage
from src.pages.product_detail_page import ProductDetailPage
from src.pages.product_listing_page import ProductListingPage
from src.pages.register_page import RegisterPage
from src.utils.credential_manager import CredentialManager

# ───────────────────────────────────────────────────────────────────
# Forensics holder
# ───────────────────────────────────────────────────────────────────


@dataclass
class _Forensics:
    """Per-test bucket of diagnostic data.

    Populated by listeners and the context/page fixtures. Read in the
    async teardown of the ``page`` fixture (when a failure has been
    flagged by the makereport hook) to decide what to attach.
    """

    console_messages: list[dict[str, Any]] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    trace_path: Path | None = None


@pytest_asyncio.fixture
async def forensics(request: pytest.FixtureRequest) -> _Forensics:
    """Per-test forensics holder, exposed on the request node.

    Stored on ``request.node`` so the async fixture teardowns can
    fetch the same instance without going through the dependency
    graph.
    """
    f = _Forensics()
    request.node._forensics = f
    return f


# ───────────────────────────────────────────────────────────────────
# Sync hook: record per-test outcome on the item
# ───────────────────────────────────────────────────────────────────


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """Stamp the test outcome onto the item for fixture teardowns.

    Async fixture teardowns cannot inspect the report directly because
    pytest only generates it inside this hook. By writing it onto
    ``item.rep_<phase>``, async teardowns running afterward can read
    ``item.rep_call.failed`` and decide whether to capture forensics.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def _test_failed(request: pytest.FixtureRequest) -> bool:
    """True if the test body failed (not setup/teardown)."""
    rep = getattr(request.node, "rep_call", None)
    return bool(rep and rep.failed)


# ───────────────────────────────────────────────────────────────────
# Browser context with tracing
# ───────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def context(
    browser: Browser,
    forensics: _Forensics,
    tmp_path_factory: pytest.TempPathFactory,
    request: pytest.FixtureRequest,
) -> AsyncGenerator[BrowserContext, None]:
    """Browser context with Playwright tracing started.

    Tracing captures network, screenshots per action, and DOM
    snapshots — everything needed to replay the test in the
    Playwright trace viewer after a failure.

    Why override the root ``context`` fixture
    -----------------------------------------
    The root version is the minimal viable context. Web tests need
    tracing, but API tests must not pay the overhead. This override
    is scoped to ``tests/web/`` and inherits the ``browser`` fixture
    from the root conftest unchanged.
    """
    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 playwright-api-web-mobile/0.1",
    )

    await ctx.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True,
    )

    trace_dir = tmp_path_factory.mktemp("traces")
    forensics.trace_path = trace_dir / "trace.zip"

    try:
        yield ctx
    finally:
        # Stop tracing FIRST so the .zip is on disk before the page
        # fixture's teardown tries to attach it.
        try:
            await ctx.tracing.stop(path=str(forensics.trace_path))
        except Exception:  # noqa: BLE001 — never let tracing teardown fail a test
            forensics.trace_path = None

        # Attach trace to Allure if the test failed. Done here rather
        # than in the page fixture because trace lifecycle is tied to
        # the context, not the page.
        if _test_failed(request) and forensics.trace_path and forensics.trace_path.exists():
            with contextlib.suppress(Exception):
                allure.attach.file(  # type: ignore[no-untyped-call]
                    str(forensics.trace_path),
                    name="Playwright trace.zip",
                    extension="zip",
                )

        await ctx.close()


# ───────────────────────────────────────────────────────────────────
# Page with console/network listeners and failure capture
# ───────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def page(
    context: BrowserContext,
    forensics: _Forensics,
    request: pytest.FixtureRequest,
) -> AsyncGenerator[Page, None]:
    """Page with console + network capture and on-failure forensics.

    Listeners populate ``forensics.console_messages`` and
    ``forensics.network_failures`` throughout the test run. On
    failure, this teardown captures the final URL, full-page
    screenshot, and rendered HTML, then attaches all collected data
    to Allure.
    """
    p = await context.new_page()

    def on_console(msg: ConsoleMessage) -> None:
        # Only error/warning are useful signal; "log"/"info"/"debug"
        # would drown the report in framework chatter.
        if msg.type in ("error", "warning"):
            forensics.console_messages.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                    "location": str(msg.location) if msg.location else None,
                }
            )

    def on_request_failed(req: Request) -> None:
        forensics.network_failures.append(
            {
                "url": req.url,
                "method": req.method,
                "failure": req.failure,
            }
        )

    p.on("console", on_console)
    p.on("requestfailed", on_request_failed)

    try:
        yield p
    finally:
        # Capture failure forensics BEFORE closing the page — the
        # page must still be alive for screenshot/content calls.
        if _test_failed(request):
            await _attach_failure_forensics(p, forensics)
        await p.close()


async def _attach_failure_forensics(p: Page, f: _Forensics) -> None:
    """Capture and attach final state when the test body failed.

    Each capture is wrapped in its own try/except: an early failure
    (e.g. page already closed) must not prevent later captures from
    running.
    """
    # Final URL — cheap, almost always available.
    with contextlib.suppress(Exception):
        allure.attach(
            p.url,
            name="Final URL",
            attachment_type=allure.attachment_type.TEXT,
        )

    # Full-page screenshot — full_page=True so vertically long pages
    # are captured in their entirety, unlike the per-step viewport
    # screenshots produced by @web_step.
    try:
        screenshot = await p.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name="Final screenshot (failure)",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:  # noqa: BLE001
        pass

    # Rendered DOM at the moment of failure. Useful for distinguishing
    # "selector wrong" from "page not in expected state".
    try:
        html = await p.content()
        allure.attach(
            html,
            name="Page HTML at failure",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception:  # noqa: BLE001
        pass

    if f.console_messages:
        allure.attach(
            json.dumps(f.console_messages, indent=2),
            name="Console errors/warnings",
            attachment_type=allure.attachment_type.JSON,
        )

    if f.network_failures:
        allure.attach(
            json.dumps(f.network_failures, indent=2),
            name="Network failures",
            attachment_type=allure.attachment_type.JSON,
        )


# ───────────────────────────────────────────────────────────────────
# Page-object fixtures (unchanged from prior conftest)
# ───────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def login_page(page: Page, credentials: CredentialManager) -> AsyncGenerator[LoginPage, None]:
    yield LoginPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def register_page(
    page: Page, credentials: CredentialManager
) -> AsyncGenerator[RegisterPage, None]:
    yield RegisterPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def listing_page(
    page: Page, credentials: CredentialManager
) -> AsyncGenerator[ProductListingPage, None]:
    yield ProductListingPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def detail_page(
    page: Page, credentials: CredentialManager
) -> AsyncGenerator[ProductDetailPage, None]:
    yield ProductDetailPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def cart_page(page: Page, credentials: CredentialManager) -> AsyncGenerator[CartPage, None]:
    yield CartPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def checkout_page(
    page: Page, credentials: CredentialManager
) -> AsyncGenerator[CheckoutPage, None]:
    yield CheckoutPage(page, credentials.web_base_url)


@pytest_asyncio.fixture
async def account_page(
    page: Page, credentials: CredentialManager
) -> AsyncGenerator[AccountPage, None]:
    yield AccountPage(page, credentials.web_base_url)
