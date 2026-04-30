"""Pydantic models for order API contracts."""

from pydantic import BaseModel, ConfigDict


class Order(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int
    invoice_number: str | None = None
    invoice_date: str | None = None
    total: float | None = None
    status: str | None = None


class OrderList(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: list[Order]


class OrderCreate(BaseModel):
    payment_method: str = "credit-card"
    payment_details: dict[str, str] | None = None
