"""Root pytest fixtures — shared across all test suites."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.utils.credential_manager import CredentialManager


@pytest.fixture(scope="session")
def credentials() -> CredentialManager:
    return CredentialManager(env="dev")


@pytest_asyncio.fixture
async def browser() -> AsyncGenerator[Browser, None]:
    """Function-scoped browser.

    Session scope would be faster but introduces event-loop binding issues:
    pytest-asyncio creates a fresh function-scoped loop for each test, and
    Playwright's transport breaks if reused across loops. Function scope
    trades ~1s of launch time per test for stable async semantics.
    """
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest_asyncio.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 playwright-api-web-mobile/0.1",
    )
    yield ctx
    await ctx.close()


@pytest_asyncio.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    new_page = await context.new_page()
    yield new_page
    await new_page.close()
