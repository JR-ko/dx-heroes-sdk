from typing import List
from uuid import UUID

from .auth import TokenManager
from .models import Offer, Product, ProductRegistered
from .request import perform_request


class ProductClient:
    def __init__(
        self, refresh_token, base_url="https://python.exercise.applifting.cz/api/v1"
    ):
        self.token_manager = TokenManager(refresh_token, base_url)
        self.base_url = base_url

    async def register_product(self, product: Product) -> ProductRegistered:
        access_token = await self.token_manager.get_access_token()
        response_data = await perform_request(
            f"{self.base_url}/products/register",
            "POST",
            access_token,
            product.model_dump(mode="json"),
        )
        return ProductRegistered(**response_data)

    async def get_product_offers(self, product_id: UUID) -> List[Offer]:
        access_token = await self.token_manager.get_access_token()
        response_data = await perform_request(
            f"{self.base_url}/products/{product_id}/offers", "GET", access_token
        )
        return [Offer(**offer_data) for offer_data in response_data]
