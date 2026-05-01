"""Faker-based data factories for test data generation.

Pattern reference: see ``src/utils/credential_manager.py`` and
``src/utils/assertions.py`` for fully commented examples of utility
modules.
"""

from faker import Faker

from src.models.user import UserCreate

fake = Faker()


def make_user(email_suffix: str = "@example.test") -> UserCreate:
    """Generate a fake user. Email uses '.test' TLD to avoid real emails."""
    return UserCreate(
        email=f"{fake.user_name()}{fake.random_int(1000, 9999)}{email_suffix}",
        password=fake.password(length=12, special_chars=True, digits=True, upper_case=True),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        address=fake.street_address(),
        city=fake.city(),
        state=fake.state(),
        country="AU",
        postcode=fake.postcode(),
        phone=fake.numerify("04########"),
        dob=fake.date_of_birth(minimum_age=21, maximum_age=70).isoformat(),
    )
