"""Web UI test fixtures."""

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
