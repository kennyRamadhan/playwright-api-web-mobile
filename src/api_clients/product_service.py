"""Product API client for Practice Software Testing."""

from typing import Any

from src.api_clients.base_service import BaseService
from src.models.product import Product, ProductCreate, ProductList


class ProductService(BaseService):
    """CRUD and listing operations for /products."""

    async def list_products(
        self,
        *,
        page: int | None = None,
        by_category: str | None = None,
        by_brand: str | None = None,
    ) -> ProductList:
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if by_category is not None:
            params["by_category"] = by_category
        if by_brand is not None:
            params["by_brand"] = by_brand
        response = await self._request("GET", "/products", params=params or None)
        return ProductList.model_validate(response.json())

    async def get_product(self, product_id: str | int) -> Product:
        response = await self._request("GET", f"/products/{product_id}")
        return Product.model_validate(response.json())

    async def create_product(self, payload: ProductCreate) -> Product:
        response = await self._request(
            "POST", "/products", json=payload, expected_status=(200, 201)
        )
        return Product.model_validate(response.json())

    async def delete_product(self, product_id: str | int) -> None:
        await self._request("DELETE", f"/products/{product_id}", expected_status=(200, 204))
