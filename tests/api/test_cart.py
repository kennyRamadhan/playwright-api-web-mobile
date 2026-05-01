"""API tests for /carts endpoints.

Pattern reference: see ``tests/api/test_auth.py`` for a fully commented
example of the API test conventions used here (Allure decorators,
AAA structure, assertion-helper choice).
"""

import allure
import pytest

from src.api_clients.base_service import APIError
from src.api_clients.cart_service import CartService
from src.api_clients.product_service import ProductService


@allure.epic("Practice Software Testing")
@allure.feature("Cart")
class TestCart:
    @allure.id("API-CART-200-001")
    @allure.title("Add product to cart returns success")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_add_product_to_cart(
        self, cart_service: CartService, product_service: ProductService
    ):
        # Arrange
        product = (await product_service.list_products()).data[0]
        cart_id = await cart_service.create_cart()

        # Act
        result = await cart_service.add_item(cart_id, product.id, quantity=1)

        # Assert
        assert "result" in result or "cart" in str(result).lower() or result == {}
        cart = await cart_service.get_cart(cart_id)
        assert cart is not None

    @allure.id("API-CART-200-002")
    @allure.title("Re-adding the same product accumulates the cart quantity")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_update_cart_item_quantity(
        self, cart_service: CartService, product_service: ProductService
    ):
        # Note: the demo has no PUT/PATCH for cart items — POSTing the same
        # product_id accumulates quantity. This test pins that behavior.
        # Arrange
        product = (await product_service.list_products()).data[0]
        cart_id = await cart_service.create_cart()
        await cart_service.add_item(cart_id, product.id, quantity=1)

        # Act
        await cart_service.update_item(cart_id, product.id, quantity=3)

        # Assert
        cart_response = await cart_service._request("GET", f"/carts/{cart_id}")
        body = cart_response.json()
        items = body.get("cart_items", [])
        assert items, "cart should have items"
        matching = [i for i in items if str(i.get("product_id")) == str(product.id)]
        assert matching, "expected re-added product to be present"
        assert matching[0]["quantity"] == 4  # 1 + 3

    @allure.id("API-CART-204-001")
    @allure.title("Remove cart item succeeds with 200/204")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_remove_cart_item(
        self, cart_service: CartService, product_service: ProductService
    ):
        # Arrange
        product = (await product_service.list_products()).data[0]
        cart_id = await cart_service.create_cart()
        await cart_service.add_item(cart_id, product.id, quantity=1)

        # Act / Assert — no exception means the request hit one of the expected codes
        await cart_service.remove_item(cart_id, product.id)

    @allure.id("API-CART-422-001")
    @allure.title("Add to cart with invalid quantity (0) returns 422")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_add_with_invalid_quantity_returns_422(
        self, cart_service: CartService, product_service: ProductService
    ):
        # Note: catalog originally specified 400; Laravel validation actually
        # returns 422 when the request advertises Accept: application/json.
        # Arrange
        product = (await product_service.list_products()).data[0]
        cart_id = await cart_service.create_cart()

        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await cart_service.add_item(cart_id, product.id, quantity=0, expected_status=200)
        assert exc_info.value.status_code == 422
