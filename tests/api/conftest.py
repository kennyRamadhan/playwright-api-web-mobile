"""API-layer fixtures — service clients and pre-authenticated tokens.

What belongs here
-----------------
Fixtures that only API tests consume. Service-client instances,
authenticated tokens for the seeded admin and customer accounts, and
any combination of the two (e.g. an ``admin_product_service`` that
arrives pre-authenticated as admin).

Why these are NOT in the root conftest
--------------------------------------
Web tests do not need API service clients. Putting these at root would
load every imported service module on every test session (including
web-only sessions) and would invite tests to mix surfaces in ways that
defeat the architectural separation.

Two flavours of service-client fixture
--------------------------------------
1. **Unauthenticated** (e.g. ``auth_service``, ``public_user_service``)
   — used by tests that exercise login/auth themselves, or tests that
   verify 401 behaviour when no token is set.

2. **Pre-authenticated** (e.g. ``admin_product_service``,
   ``customer_order_service``) — used by tests that need a logged-in
   client and don't want to repeat the login dance. The fixture
   handles login internally and yields a client with the token already
   set.

Why ``yield`` then ``await service.close()``
--------------------------------------------
The yield-then-cleanup pattern guarantees the underlying httpx
connection pool is released even if the test raises. Without this,
long test sessions accumulate sockets and eventually exhaust file
descriptors on slower CI runners.

Pattern reference for: any future API-layer fixture additions.
"""

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
    """Unauthenticated AuthService.

    Use this when the test itself performs the login (e.g. login flow
    tests). For tests that need a pre-authenticated client, use the
    ``admin_token`` or ``customer_token`` fixtures and a separate
    service-client fixture.
    """
    service = AuthService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_token(credentials: CredentialManager) -> str:
    """A fresh access token for the seeded admin account.

    Each test gets its own token via a function-scoped fixture. Caching
    the token at session scope is a common optimization, but the demo
    backend is unstable enough under sustained load that a fresh login
    per test reduces flake more than the saved time would gain.

    The fixture closes its own throwaway AuthService in a try/finally
    so a login error doesn't leak the connection.
    """
    service = AuthService(base_url=credentials.api_base_url)
    try:
        result = await service.login(credentials.admin_email, credentials.admin_password)
        return result.access_token
    finally:
        await service.close()


@pytest_asyncio.fixture
async def customer_token(credentials: CredentialManager) -> str:
    """Same as ``admin_token`` but for the seeded customer account."""
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
    """Public ProductService (no auth) — for read-only listing/search tests."""
    service = ProductService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_product_service(
    credentials: CredentialManager,
    admin_token: str,
) -> AsyncGenerator[ProductService, None]:
    """ProductService pre-authenticated as admin.

    Used by tests that mutate products (create / update / delete). The
    ``admin_token`` dependency triggers a login automatically; pytest
    resolves the dependency graph from parameter names.
    """
    service = ProductService(base_url=credentials.api_base_url)
    service.set_token(admin_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def cart_service(
    credentials: CredentialManager,
) -> AsyncGenerator[CartService, None]:
    """Public CartService — cart creation does not require auth on this demo."""
    service = CartService(base_url=credentials.api_base_url)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def customer_order_service(
    credentials: CredentialManager,
    customer_token: str,
) -> AsyncGenerator[OrderService, None]:
    """OrderService pre-authenticated as customer (the typical buyer identity)."""
    service = OrderService(base_url=credentials.api_base_url)
    service.set_token(customer_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def admin_user_service(
    credentials: CredentialManager,
    admin_token: str,
) -> AsyncGenerator[UserService, None]:
    """UserService pre-authenticated as admin — for ``GET /users`` listing tests."""
    service = UserService(base_url=credentials.api_base_url)
    service.set_token(admin_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def customer_user_service(
    credentials: CredentialManager,
    customer_token: str,
) -> AsyncGenerator[UserService, None]:
    """UserService pre-authenticated as customer — for ``GET /users/me`` tests."""
    service = UserService(base_url=credentials.api_base_url)
    service.set_token(customer_token)
    yield service
    await service.close()


@pytest_asyncio.fixture
async def public_user_service(
    credentials: CredentialManager,
) -> AsyncGenerator[UserService, None]:
    """Unauthenticated UserService — used to verify 401 on protected endpoints."""
    service = UserService(base_url=credentials.api_base_url)
    yield service
    await service.close()
