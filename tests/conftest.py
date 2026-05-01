"""Test-level shared fixtures — for fixtures used by both API and Web tests.

This conftest sits between the repo-root conftest (browser, page,
credentials) and the surface-specific conftests (tests/api/conftest.py,
tests/web/conftest.py).

What belongs here
-----------------
Fixtures that are used across surfaces but are conceptually
test-data / test-input concerns (not infrastructure). The canonical
example is ``random_user`` — both API tests (``test_register_creates_user``)
and Web tests (``test_register_*``) need a fresh user payload.

What does NOT belong here
-------------------------
- Browser / page / API-client primitives → root conftest or surface conftest
- Tokens or pre-authenticated clients → surface conftest (API only)

See ``docs/CONFTEST_GUIDE.md`` for the full decision tree.
"""

import pytest

from src.models.user import UserCreate
from src.utils.data_factory import make_user


@pytest.fixture
def random_user() -> UserCreate:
    """A freshly generated, unique user payload.

    Function-scoped (default) so each test gets its own user — important
    because registration is non-idempotent: the same email cannot be
    registered twice. Session scope would create cross-test pollution.
    """
    return make_user()
