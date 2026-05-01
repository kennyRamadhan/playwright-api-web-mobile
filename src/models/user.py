"""Pydantic models for user-related API contracts.

Why Pydantic models instead of raw dicts
----------------------------------------
1. **Schema validation on construction.** A response that's missing
   ``access_token`` raises ``ValidationError`` at the moment the model
   is built — clearly pointing to the contract violation. Without a
   model, the test would crash later as a confusing ``KeyError`` deep
   in an assertion.

2. **Editor autocomplete in tests.** ``response.access_token`` is a
   typed attribute; ``response["access_token"]`` is a string lookup.
   The first one catches typos at edit time.

3. **Self-documenting API contract.** The model definition IS the
   documentation of what the endpoint returns — no separate doc to
   drift out of sync.

When to add to this file
------------------------
Group models by resource family (user, product, cart, order). If a
new endpoint relates to users (e.g. password reset), add request/response
models here. If it spans multiple resources (e.g. a user's order
history), put it in the file that matches the primary resource.

Why ``extra="allow"`` on response models
----------------------------------------
The demo backend sometimes adds new fields without warning. ``extra="allow"``
means the model accepts unknown fields silently — old tests stay green
when the server adds a new field, while still catching missing or
wrong-typed fields we DO validate. Request models do not need this
(we control the body).

Pattern reference for: every other model file in ``src/models/``.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """POST ``/users/login`` request body.

    ``EmailStr`` enforces RFC-compliant email format at construction
    time — catches a typo'd test-data factory before the request even
    reaches the network.
    """

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """POST ``/users/login`` successful response.

    Practice Software Testing returns: ``access_token``, ``token_type``,
    ``expires_in``. Other fields (e.g. ``refresh_expires_in`` in some
    versions) are accepted via ``extra="allow"`` but not validated.
    """

    model_config = ConfigDict(extra="allow")

    access_token: str
    # Default "Bearer" matches the demo backend's typical response.
    # The lower-case form is also seen — tests should compare
    # case-insensitively (see ``test_valid_login_returns_token``).
    token_type: str = "Bearer"
    expires_in: int


class User(BaseModel):
    """A user record as returned by ``GET /users/me`` and ``GET /users``.

    ``id`` is typed as ``str | int`` because the demo's user list
    endpoint and current-user endpoint historically returned different
    types. Accepting both avoids brittle test failures on a non-issue.
    """

    model_config = ConfigDict(extra="allow")

    id: str | int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None


class UserCreate(BaseModel):
    """POST ``/users/register`` request body.

    Most fields are optional in this model (``... | None = None``) so
    test-data factories can build a minimal user and only fill the
    fields a particular test cares about. The web register form
    requires more fields than the API does — see ``RegisterPage.register``
    for the full set of front-end-required fields.

    ``password`` enforces ``min_length=8`` to fail fast on factory
    misconfiguration before the request hits the API.
    """

    email: str
    password: str = Field(min_length=8)
    first_name: str
    last_name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postcode: str | None = None
    phone: str | None = None
    dob: str | None = None
