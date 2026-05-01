"""OrderService — Practice Software Testing /invoices endpoints (modelled as orders).

Pattern reference: see ``src/api_clients/auth_service.py`` for a fully
commented example of the ``BaseService`` client pattern.
"""

from typing import Any

from src.api_clients.base_service import BaseService
from src.models.order import Order, OrderList


class OrderService(BaseService):
    """Practice Software Testing exposes invoices as the order resource.

    The API expects:
    - billing_street / city / state / country / postcode
    - payment_method (bank-transfer is the most reliable default)
    - payment_details: nested object with method-specific fields
    """

    DEFAULT_BANK_DETAILS = {
        "bank_name": "First Test Bank",
        "account_name": "Kenny Tester",
        "account_number": "1234567890",
    }

    async def create_order(
        self,
        *,
        cart_id: str,
        billing_street: str = "10 Downing Street",
        billing_city: str = "London",
        billing_state: str = "Greater London",
        billing_country: str = "UK",
        billing_postcode: str = "SW1A 2AA",
        payment_method: str = "bank-transfer",
        payment_details: dict[str, str] | None = None,
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> Order:
        payload: dict[str, Any] = {
            "cart_id": cart_id,
            "billing_street": billing_street,
            "billing_city": billing_city,
            "billing_state": billing_state,
            "billing_country": billing_country,
            "billing_postcode": billing_postcode,
            "payment_method": payment_method,
            "payment_details": payment_details or self.DEFAULT_BANK_DETAILS,
        }
        response = await self._request(
            "POST", "/invoices", json=payload, expected_status=expected_status
        )
        return Order.model_validate(response.json())

    async def get_order(self, order_id: str | int) -> Order:
        response = await self._request("GET", f"/invoices/{order_id}")
        return Order.model_validate(response.json())

    async def list_orders(self) -> OrderList:
        response = await self._request("GET", "/invoices")
        body = response.json()
        if isinstance(body, list):
            body = {"data": body}
        return OrderList.model_validate(body)
