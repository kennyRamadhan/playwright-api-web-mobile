"""Test-level shared fixtures."""

import pytest

from src.models.user import UserCreate
from src.utils.data_factory import make_user


@pytest.fixture
def random_user() -> UserCreate:
    return make_user()
