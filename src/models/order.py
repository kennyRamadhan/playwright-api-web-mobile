"""Pydantic models for order API contracts.

Pattern reference: see ``src/models/user.py`` for a fully commented
example of the model conventions used here.
"""

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
