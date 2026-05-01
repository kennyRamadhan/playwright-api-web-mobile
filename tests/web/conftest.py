"""Web-layer fixtures — page-object instances bound to the shared Page.

What belongs here
-----------------
Fixtures that construct page-object instances. Each fixture takes the
shared ``page`` (defined at the repo root) and the session-scoped
``credentials``, then builds the page object.

Why these are NOT in the root conftest
--------------------------------------
API tests do not need page objects. The browser fixture chain
(``browser`` → ``context`` → ``page``) costs ~1 s of launch time per
test. Keeping the page-object fixtures here signals that this cost
should only be paid by web tests.

Why ``yield`` instead of ``return``
-----------------------------------
Page objects do not own their own resources (the browser, context, and
page are owned by their respective fixtures higher up the chain), so
``return`` would technically work. ``yield`` is used for consistency
with the API conftest pattern and to leave room for future per-page
teardown logic without changing the fixture signatures.

Pattern reference for: any future page-object fixture additions.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from playwright.async_api import Page

from src.pages.account_page import AccountPage
from src.pages.cart_page import CartPage
from src.pages.checkout_page import CheckoutPage
from src.pages.login_page import LoginPage
from src.pages.product_detail_page import ProductDetailPage
from src.pages.product_listing_page import ProductListingPage
from src.pages.register_page import RegisterPage
from src.utils.credential_manager import CredentialManager


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
