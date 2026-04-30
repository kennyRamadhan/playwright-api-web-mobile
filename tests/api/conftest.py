"""API test fixtures."""

from collections.abc import AsyncGenerator

import pytest_asyncio

from src.api_clients.auth_service import AuthService
from src.api_clients.cart_service import CartService
from src.api_clients.order_service import OrderService
from src.api_clients.product_service import ProductService
from src.api_clients.user_service import UserService
from src.utils.credential_manager import CredentialManager


@pytest_asyncio.fixture
async def auth_service(
    credentials: CredentialManager,
) -> AsyncGenerator[AuthService, None]:
    service = AuthService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_token(credentials: CredentialManager) -> str:
    service = AuthService(base_url=credentials.api_base_url)
    try:
        result = await service.login(credentials.admin_email, credentials.admin_password)
        return result.access_token
    finally:
        await service.close()


@pytest_asyncio.fixture
async def customer_token(credentials: CredentialManager) -> str:
    service = AuthService(base_url=credentials.api_base_url)
    try:
        result = await service.login(credentials.customer_email, credentials.customer_password)
        return result.access_token
    finally:
        await service.close()


@pytest_asyncio.fixture
async def product_service(
    credentials: CredentialManager,
) -> AsyncGenerator[ProductService, None]:
    service = ProductService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_product_service(
    credentials: CredentialManager,
    admin_token: str,
) -> AsyncGenerator[ProductService, None]:
    service = ProductService(base_url=credentials.api_base_url)
    service.set_token(admin_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def cart_service(
    credentials: CredentialManager,
) -> AsyncGenerator[CartService, None]:
    service = CartService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def customer_order_service(
    credentials: CredentialManager,
    customer_token: str,
) -> AsyncGenerator[OrderService, None]:
    service = OrderService(base_url=credentials.api_base_url)
    service.set_token(customer_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_user_service(
    credentials: CredentialManager,
    admin_token: str,
) -> AsyncGenerator[UserService, None]:
    service = UserService(base_url=credentials.api_base_url)
    service.set_token(admin_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def customer_user_service(
    credentials: CredentialManager,
    customer_token: str,
) -> AsyncGenerator[UserService, None]:
    service = UserService(base_url=credentials.api_base_url)
    service.set_token(customer_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def public_user_service(
    credentials: CredentialManager,
) -> AsyncGenerator[UserService, None]:
    service = UserService(base_url=credentials.api_base_url)
    yield service
    await service.close()
