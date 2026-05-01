"""AccountPage — /account, post-login dashboard.

Pattern reference: see ``src/pages/login_page.py`` for a fully commented
example of the page-object pattern used here.
"""

import allure
from playwright.async_api import Locator

from src.pages.base_page import BasePage


class AccountPage(BasePage):
    URL_PATH = "/account"

    @property
    def page_heading(self) -> Locator:
        return self.by_test_id("page-title")

    @property
    def nav_menu(self) -> Locator:
        return self.by_test_id("nav-menu")

    @allure.step("Check account page is loaded")
    async def is_loaded(self) -> bool:
        await self._page.wait_for_url("**/account**", timeout=10_000)
        return True
