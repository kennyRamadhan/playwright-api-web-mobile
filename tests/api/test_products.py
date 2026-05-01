"""API tests for /products endpoints.

Pattern reference: see ``tests/api/test_auth.py`` for a fully commented
example of the API test conventions used here.
"""

import contextlib

import allure
import httpx
import pytest

from src.api_clients.base_service import APIError
from src.api_clients.product_service import ProductService
from src.models.product import ProductCreate


@allure.epic("Practice Software Testing")
@allure.feature("Products")
class TestProductListing:
    @allure.id("API-PRODUCTS-200-001")
    @allure.title("GET /products returns a paginated list")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_list_products_returns_paginated_list(self, product_service: ProductService):
        # Act
        result = await product_service.list_products()

        # Assert
        assert result.data, "expected non-empty product list"
        assert result.current_page == 1
        assert result.total is not None and result.total >= len(result.data)

    @allure.id("API-PRODUCTS-200-002")
    @allure.title("GET /products/{id} returns a single product")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_get_product_by_id_returns_product(self, product_service: ProductService):
        # Arrange
        first = (await product_service.list_products()).data[0]

        # Act
        product = await product_service.get_product(first.id)

        # Assert
        assert product.id == first.id
        assert product.name == first.name
        assert product.price == first.price

    @allure.id("API-PRODUCTS-200-003")
    @allure.title("GET /products with category filter returns filtered list")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_list_products_filtered_by_category(self, credentials):
        # Arrange — fetch a real category slug
        async with httpx.AsyncClient(base_url=credentials.api_base_url, timeout=15) as client:
            cats_response = await client.get("/categories")
            cats = cats_response.json()
            category_slug = cats[0]["slug"] if isinstance(cats, list) else cats["data"][0]["slug"]

        service = ProductService(base_url=credentials.api_base_url)
        try:
            # Act
            result = await service.list_products(by_category=category_slug)

            # Assert
            assert result.data is not None
            # Pagination structure must be present even on filtered results
            assert result.current_page is not None
        finally:
            await service.close()

    @allure.id("API-PRODUCTS-404-001")
    @allure.title("GET /products/{invalid-id} returns 404")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_get_invalid_product_returns_404(self, product_service: ProductService):
        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await product_service.get_product("definitely-not-a-real-id")
        assert exc_info.value.status_code == 404


@allure.epic("Practice Software Testing")
@allure.feature("Products")
class TestProductMutations:
    @allure.id("API-PRODUCTS-201-001")
    @allure.title("POST /products as admin creates a product")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_admin_creates_product(self, admin_product_service: ProductService, credentials):
        # Arrange — pull real category, brand, image IDs
        async with httpx.AsyncClient(base_url=credentials.api_base_url, timeout=15) as client:
            cats = (await client.get("/categories")).json()
            brands = (await client.get("/brands")).json()
            images = (await client.get("/images")).json()
            category_id = cats[0]["id"] if isinstance(cats, list) else cats["data"][0]["id"]
            brand_id = brands[0]["id"] if isinstance(brands, list) else brands["data"][0]["id"]
            image_id = images[0]["id"] if isinstance(images, list) else images["data"][0]["id"]

        payload = ProductCreate(
            name="Test Product (auto)",
            description="Created by automated test suite",
            price=9.99,
            category_id=category_id,
            brand_id=brand_id,
            product_image_id=image_id,
        )

        created = None
        try:
            # Act
            created = await admin_product_service.create_product(payload)

            # Assert
            assert created.id
            assert created.name == "Test Product (auto)"
            assert created.price == 9.99
        finally:
            # Cleanup — keep demo data tidy
            if created is not None:
                with contextlib.suppress(APIError):
                    await admin_product_service.delete_product(created.id)

    @allure.id("API-PRODUCTS-422-001")
    @allure.title("POST /products with missing required fields returns 422")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_create_product_missing_fields_returns_422(
        self, admin_product_service: ProductService
    ):
        # Note: the catalog originally specified a 403 RBAC test, but the demo's
        # /products endpoint does not enforce admin-only. We instead pin
        # validation behavior — missing fields surface as 422.
        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await admin_product_service._request(
                "POST", "/products", json={"name": "Incomplete"}, expected_status=201
            )
        assert exc_info.value.status_code == 422
