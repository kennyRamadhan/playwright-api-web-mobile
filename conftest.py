"""Root-level pytest fixtures — shared across every test in the repo.

This is the highest conftest in the hierarchy. Anything defined here is
visible to every test under ``tests/`` (api, web, and future mobile).

What lives here
---------------
- ``credentials`` — session-scoped CredentialManager
- ``browser`` / ``context`` / ``page`` — Playwright primitives

Why ``credentials`` is session-scoped
-------------------------------------
Reading YAML and ``.env`` is read-only and idempotent. Doing it once
per pytest invocation saves time across hundreds of tests and makes
the credentials object identity-stable (handy if any code wants to
cache config-derived state).

Why ``browser`` / ``context`` / ``page`` are function-scoped
------------------------------------------------------------
Session scope would be faster, but pytest-asyncio creates a fresh
event loop per test function. Playwright's transport breaks if reused
across loops — you get cryptic ``AttributeError: 'NoneType' object has
no attribute 'send'`` errors deep inside Playwright's IPC. Function
scope trades ~1s of launch overhead per test for stable async
semantics, which is the right tradeoff for a CI suite that runs
tens-not-thousands of tests.

Pattern reference for: ``tests/conftest.py``, ``tests/api/conftest.py``,
``tests/web/conftest.py``. See ``docs/CONFTEST_GUIDE.md`` for the full
hierarchy explanation.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.utils.credential_manager import CredentialManager


@pytest.fixture(scope="session")
def credentials() -> CredentialManager:
    """Session-wide credentials/config object.

    Constructed once per pytest run. The ``env`` choice is hardcoded to
    "dev" for now; a future ``--env`` CLI option could make this
    configurable per invocation.
    """
    return CredentialManager(env="dev")


@pytest_asyncio.fixture
async def browser() -> AsyncGenerator[Browser, None]:
    """Function-scoped headless Chromium.

    Headless because (a) CI has no display, (b) headed adds startup
    latency without diagnostic value at this scale. Tests that need
    visual debugging should run locally with ``PWDEBUG=1`` or use the
    Playwright Inspector — not change this fixture.
    """
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest_asyncio.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Fresh browser context per test = isolated cookies, storage, cache.

    Viewport is fixed at 1280x720 so visual snapshots stay deterministic
    across machines. The user-agent is identifiable so server-side logs
    can distinguish CI traffic from real users — courtesy to the
    Practice Software Testing demo maintainers.
    """
    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 playwright-api-web-mobile/0.1",
    )
    yield ctx
    await ctx.close()


@pytest_asyncio.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """The Playwright Page object that page-object fixtures consume.

    Defined here at root rather than in tests/web/conftest.py because
    nothing below this level needs to know HOW the page is constructed
    — only that it exists. This keeps the web conftest focused on
    page-object plumbing.
    """
    new_page = await context.new_page()
    yield new_page
    await new_page.close()
