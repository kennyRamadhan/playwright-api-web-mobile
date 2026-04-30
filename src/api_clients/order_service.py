"""Order/Invoice API client for Practice Software Testing."""

from typing import Any

from src.api_clients.base_service import BaseService
from src.models.order import Order, OrderList


class OrderService(BaseService):
    """Practice Software Testing exposes invoices as the order resource."""

    async def create_order(
        self,
        *,
        cart_id: str,
        billing_address: str = "10 Downing Street",
        billing_city: str = "London",
        billing_state: str = "Greater London",
        billing_country: str = "UK",
        billing_postcode: str = "SW1A 2AA",
        payment_method: str = "credit-card",
        payment_account_name: str = "Kenny Tester",
        payment_account_number: str = "1234-5678-9012-3456",
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> Order:
        payload: dict[str, Any] = {
            "cart_id": cart_id,
            "billing_address": billing_address,
            "billing_city": billing_city,
            "billing_state": billing_state,
            "billing_country": billing_country,
            "billing_postcode": billing_postcode,
            "payment_method": payment_method,
            "payment_account_name": payment_account_name,
            "payment_account_number": payment_account_number,
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
