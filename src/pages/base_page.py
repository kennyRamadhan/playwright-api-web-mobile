"""BasePage — foundation for all page objects."""

from __future__ import annotations

import allure
from playwright.async_api import Locator, Page


class BasePage:
    """Common methods for all page objects.

    Subclasses define page-specific selectors and actions.
    """

    URL_PATH: str = ""

    def __init__(self, page: Page, base_url: str) -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")

    @property
    def page(self) -> Page:
        return self._page

    @property
    def base_url(self) -> str:
        return self._base_url

    async def goto(self, path: str | None = None) -> None:
        target = path if path is not None else self.URL_PATH
        with allure.step(f"Navigate to {target}"):
            await self._page.goto(f"{self._base_url}{target}")

    @allure.step("Check page is loaded")
    async def is_loaded(self) -> bool:
        return bool(await self._page.title())

    def by_test_id(self, test_id: str) -> Locator:
        """Locate by data-test attribute (Practice Software Testing convention)."""
        return self._page.locator(f"[data-test='{test_id}']")

    @allure.step("Capture screenshot: {name}")
    async def take_screenshot(self, name: str) -> None:
        screenshot = await self._page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
