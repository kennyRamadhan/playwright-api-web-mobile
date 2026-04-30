"""Cart API client for Practice Software Testing."""

from typing import Any

from src.api_clients.base_service import BaseService
from src.models.cart import Cart


class CartService(BaseService):
    """Operations for /carts and /carts/{id}/items."""

    async def create_cart(self) -> str:
        """Create empty cart, return cart ID."""
        response = await self._request("POST", "/carts", expected_status=(200, 201))
        body: dict[str, Any] = response.json()
        return str(body.get("id"))

    async def get_cart(self, cart_id: str) -> Cart:
        response = await self._request("GET", f"/carts/{cart_id}")
        return Cart.model_validate(response.json())

    async def add_item(
        self,
        cart_id: str,
        product_id: str | int,
        quantity: int = 1,
        *,
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> dict[str, Any]:
        body = {"product_id": product_id, "quantity": quantity}
        response = await self._request(
            "POST",
            f"/carts/{cart_id}",
            json=body,
            expected_status=expected_status,
        )
        result: dict[str, Any] = response.json() if response.content else {}
        return result

    async def update_item(
        self,
        cart_id: str,
        product_id: str | int,
        quantity: int,
    ) -> dict[str, Any]:
        """Practice Software Testing has no PUT — POSTing the same product
        accumulates quantity. This wrapper preserves the semantic name."""
        return await self.add_item(cart_id, product_id, quantity)

    async def remove_item(self, cart_id: str, product_id: str | int) -> None:
        await self._request(
            "DELETE",
            f"/carts/{cart_id}/product/{product_id}",
            expected_status=(200, 204),
        )
