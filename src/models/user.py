"""Pydantic models for user-related API contracts."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """POST /users/login successful response.

    Practice Software Testing returns: access_token, token_type, expires_in.
    """

    model_config = ConfigDict(extra="allow")

    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class User(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None


class UserCreate(BaseModel):
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
