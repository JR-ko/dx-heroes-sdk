from typing import List
from uuid import UUID

from .auth import TokenManager
from .models import Offer, Product, ProductRegistered


class ProductClient:
    def __init__(
        self, refresh_token, base_url="https://python.exercise.applifting.cz/api/v1"
    ):
        self.token_manager = TokenManager(refresh_token, base_url)
        self.base_url = base_url

    async def register_product(self, product: Product) -> ProductRegistered:
        response_data = await self.token_manager.execute_authenticated_request(
            f"{self.base_url}/products/register",
            "POST",
            product.model_dump(mode="json"),
        )
        return ProductRegistered(**response_data)

    async def get_product_offers(self, product_id: UUID) -> List[Offer]:
        response_data = await self.token_manager.execute_authenticated_request(
            f"{self.base_url}/products/{product_id}/offers", "GET"
        )
        return [Offer(**offer_data) for offer_data in response_data]
