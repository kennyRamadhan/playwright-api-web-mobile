"""Pydantic models for cart API contracts."""

from pydantic import BaseModel, ConfigDict


class CartItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    product_id: str | int
    quantity: int
    price: float | None = None


class Cart(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int | None = None
    items: list[CartItem] = []
    total: float | None = None


class CartCreate(BaseModel):
    """POST /carts request body — server creates an empty cart."""


class CartItemAdd(BaseModel):
    product_id: str | int
    quantity: int


class CartItemUpdate(BaseModel):
    quantity: int
