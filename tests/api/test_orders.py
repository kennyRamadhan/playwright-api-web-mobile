"""API tests for /invoices endpoints (Practice Software Testing's 'orders')."""

import allure
import pytest

from src.api_clients.base_service import APIError
from src.api_clients.cart_service import CartService
from src.api_clients.order_service import OrderService
from src.api_clients.product_service import ProductService


async def _seed_cart_with_item(cart_service: CartService, product_service: ProductService) -> str:
    product = (await product_service.list_products()).data[0]
    cart_id = await cart_service.create_cart()
    await cart_service.add_item(cart_id, product.id, quantity=1)
    return cart_id


@allure.epic("Practice Software Testing")
@allure.feature("Orders")
class TestOrders:
    @allure.id("API-ORDERS-201-001")
    @allure.title("Create invoice from cart returns 201 with invoice number")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_create_order_from_cart(
        self,
        customer_order_service: OrderService,
        cart_service: CartService,
        product_service: ProductService,
    ):
        # Arrange
        cart_id = await _seed_cart_with_item(cart_service, product_service)

        # Act
        order = await customer_order_service.create_order(cart_id=cart_id)

        # Assert
        assert order.id
        assert order.invoice_number and order.invoice_number.startswith("INV-")

    @allure.id("API-ORDERS-200-001")
    @allure.title("GET /invoices/{id} returns order details")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_order_by_id(
        self,
        customer_order_service: OrderService,
        cart_service: CartService,
        product_service: ProductService,
    ):
        # Arrange — seed an order
        cart_id = await _seed_cart_with_item(cart_service, product_service)
        created = await customer_order_service.create_order(cart_id=cart_id)

        # Act
        fetched = await customer_order_service.get_order(created.id)

        # Assert
        assert fetched.id == created.id
        assert fetched.invoice_number == created.invoice_number

    @allure.id("API-ORDERS-200-002")
    @allure.title("GET /invoices returns the user's order history")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_list_orders(
        self,
        customer_order_service: OrderService,
        cart_service: CartService,
        product_service: ProductService,
    ):
        # Arrange — guarantee at least one order exists
        cart_id = await _seed_cart_with_item(cart_service, product_service)
        await customer_order_service.create_order(cart_id=cart_id)

        # Act
        history = await customer_order_service.list_orders()

        # Assert
        assert len(history.data) >= 1

    @allure.id("API-ORDERS-422-001")
    @allure.title("Create invoice without payment_details returns 422")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_create_order_without_payment_details_returns_422(
        self,
        customer_order_service: OrderService,
        cart_service: CartService,
        product_service: ProductService,
    ):
        # Note: the demo accepts empty carts (silently produces an empty
        # invoice), so we instead validate the missing-payment_details path.
        # Arrange
        cart_id = await _seed_cart_with_item(cart_service, product_service)

        # Act / Assert — call the underlying request directly to skip required defaults
        with pytest.raises(APIError) as exc_info:
            await customer_order_service._request(
                "POST",
                "/invoices",
                json={
                    "cart_id": cart_id,
                    "billing_street": "1 St",
                    "billing_city": "X",
                    "billing_state": "Y",
                    "billing_country": "AU",
                    "billing_postcode": "00000",
                    "payment_method": "bank-transfer",
                    # payment_details intentionally omitted
                },
                expected_status=201,
            )
        assert exc_info.value.status_code == 422
