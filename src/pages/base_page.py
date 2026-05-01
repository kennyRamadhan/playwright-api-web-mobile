"""BasePage — foundation class for all Playwright page objects in this codebase.

Architectural role
------------------
``BasePage`` is to web tests what ``BaseService`` is to API tests: a
single foundation that owns the boilerplate (Playwright ``Page`` handle,
base URL, navigation, locator helper) so subclasses can be tiny and
focused on the page they represent.

When to extend
--------------
For each distinct page (or coherent UI region) of the application
under test, create one subclass. See ``login_page.py`` for the
canonical example of how a subclass is structured.

Page Object Model discipline
----------------------------
- Selectors live on the page class as ``@property`` getters returning
  ``Locator``. They never appear in tests.
- Action methods are user-action-named (``login``, ``add_to_cart``),
  not implementation-named (``click_login_button``).
- Action methods return ``None`` or a value that supports the
  test's assertion — never the raw ``Locator``.
- Tests interact with pages via methods, not by reaching into the
  ``Page`` object directly.

Related files
-------------
- ``src/pages/login_page.py`` — canonical example subclass
- ``tests/web/conftest.py`` — fixtures that instantiate concrete pages
- ``ARCHITECTURE.md`` — design rationale for POM choice in this repo
"""

from __future__ import annotations

import allure
from playwright.async_api import Locator, Page


class BasePage:
    """Common methods every page object inherits.

    Subclasses define page-specific selectors (as ``@property``) and
    user actions (as ``async def`` methods).

    Inheritance contract
    --------------------
    - Subclasses MUST set ``URL_PATH`` if the page is reachable by
      direct navigation. ``goto()`` uses it as the default target.
    - Subclasses SHOULD override ``is_loaded`` with a concrete
      readiness check (e.g. wait for a unique element) instead of
      relying on the title-only default below.
    """

    # Subclasses override to declare their direct URL. Empty string is
    # valid for pages that are only reachable via in-app navigation.
    URL_PATH: str = ""

    def __init__(self, page: Page, base_url: str) -> None:
        self._page = page
        # Strip trailing slash to match how URL_PATH starts with "/".
        self._base_url = base_url.rstrip("/")

    @property
    def page(self) -> Page:
        """Underlying Playwright Page. Tests should rarely need this directly,
        but it's exposed so tests can perform whole-page operations like
        ``page.wait_for_url()`` without forcing a method on every subclass."""
        return self._page

    @property
    def base_url(self) -> str:
        return self._base_url

    async def goto(self, path: str | None = None) -> None:
        """Navigate to ``path`` (or the subclass's ``URL_PATH``).

        Wrapped in a body-level ``allure.step`` rather than the decorator
        form because allure-pytest's ``@allure.step`` stringifies args
        before formatting and cannot resolve ``{self.URL_PATH}``.
        Body-level lets us include the actual target URL in the step
        name, which is more useful in the report anyway.
        """
        target = path if path is not None else self.URL_PATH
        with allure.step(f"Navigate to {target}"):
            await self._page.goto(f"{self._base_url}{target}")

    @allure.step("Check page is loaded")
    async def is_loaded(self) -> bool:
        """Default readiness probe: page has produced a non-empty title.

        Subclasses should override with something page-specific (e.g.
        wait for the email input to be visible) — title alone is too
        loose for SPA pages where the route changes but the title lags.
        """
        return bool(await self._page.title())

    def by_test_id(self, test_id: str) -> Locator:
        """Locate by ``[data-test='...']`` — the convention used throughout
        Practice Software Testing's frontend.

        Sync (not async) because ``page.locator(...)`` is itself sync;
        the resolution of the selector against the DOM is lazy and
        happens on the first action against the returned ``Locator``.
        """
        return self._page.locator(f"[data-test='{test_id}']")

    @allure.step("Capture screenshot: {name}")
    async def take_screenshot(self, name: str) -> None:
        """Capture a full-page screenshot and attach it to the Allure step.

        Used by tests as a manual diagnostic aid; the CI also captures
        screenshots automatically on test failure via the Allure plugin's
        hook (see ``pyproject.toml`` configuration).
        """
        screenshot = await self._page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
