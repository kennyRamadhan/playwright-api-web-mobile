"""Pydantic models for product API contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class Product(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int
    name: str
    description: str | None = None
    price: float
    is_location_offer: bool | None = None
    is_rental: bool | None = None
    in_stock: bool | None = None
    category_id: str | int | None = None
    brand_id: str | int | None = None
    product_image_id: str | int | None = None


class ProductList(BaseModel):
    """Laravel-style paginated response."""

    model_config = ConfigDict(extra="allow")

    data: list[Product]
    current_page: int | None = None
    total: int | None = None
    per_page: int | None = None
    last_page: int | None = None


class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category_id: str | int
    brand_id: str | int
    product_image_id: str | int
    is_location_offer: bool = False
    is_rental: bool = False


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    description: str | None = None
    price: float | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
