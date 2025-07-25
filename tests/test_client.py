from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.client import ProductClient
from src.models import Offer, Product, ProductRegistered


@pytest.fixture
def product_client():
    return ProductClient("test_refresh_token")


@pytest.fixture
def sample_product():
    return Product(
        id=uuid4(), name="Test Product", description="A test product description"
    )


@pytest.fixture
def sample_product_registered():
    return ProductRegistered(id=uuid4())


@pytest.fixture
def sample_offers():
    return [
        Offer(id=uuid4(), price=100, items_in_stock=10),
        Offer(id=uuid4(), price=150, items_in_stock=5),
    ]


class TestProductClient:
    def test_init_default_base_url(self):
        client = ProductClient("test_token")
        assert client.base_url == "https://python.exercise.applifting.cz/api/v1"
        assert client.token_manager.refresh_token == "test_token"
        assert (
            client.token_manager.base_url
            == "https://python.exercise.applifting.cz/api/v1"
        )

    def test_init_custom_base_url(self):
        custom_url = "https://custom.api.com/v2"
        client = ProductClient("test_token", custom_url)
        assert client.base_url == custom_url
        assert client.token_manager.base_url == custom_url

    @pytest.mark.asyncio
    async def test_register_product_success(self, product_client, sample_product):
        expected_response = {"id": str(sample_product.id)}

        with patch.object(
            product_client.token_manager,
            "execute_authenticated_request",
            return_value=expected_response,
        ) as mock_request:
            result = await product_client.register_product(sample_product)

            mock_request.assert_called_once_with(
                f"{product_client.base_url}/products/register",
                "POST",
                sample_product.model_dump(mode="json"),
            )
            assert isinstance(result, ProductRegistered)
            assert result.id == UUID(expected_response.get("id"))

    @pytest.mark.asyncio
    async def test_get_product_offers_success(self, product_client, sample_offers):
        product_id = uuid4()
        offers_data = [
            {
                "id": str(offer.id),
                "price": offer.price,
                "items_in_stock": offer.items_in_stock,
            }
            for offer in sample_offers
        ]

        with patch.object(
            product_client.token_manager,
            "execute_authenticated_request",
            return_value=offers_data,
        ) as mock_request:
            result = await product_client.get_product_offers(product_id)

            mock_request.assert_called_once_with(
                f"{product_client.base_url}/products/{product_id}/offers", "GET"
            )
            assert len(result) == 2
            assert all(isinstance(offer, Offer) for offer in result)
            assert result[0].id == sample_offers[0].id
            assert result[0].price == sample_offers[0].price
            assert result[0].items_in_stock == sample_offers[0].items_in_stock

    @pytest.mark.asyncio
    async def test_register_product_authentication_error_propagation(
        self, product_client, sample_product
    ):
        with patch.object(
            product_client.token_manager,
            "execute_authenticated_request",
            side_effect=Exception("Authentication failed"),
        ):
            with pytest.raises(Exception, match="Authentication failed"):
                await product_client.register_product(sample_product)

    @pytest.mark.asyncio
    async def test_get_product_offers_authentication_error_propagation(
        self, product_client
    ):
        product_id = uuid4()

        with patch.object(
            product_client.token_manager,
            "execute_authenticated_request",
            side_effect=Exception("Authentication failed"),
        ):
            with pytest.raises(Exception, match="Authentication failed"):
                await product_client.get_product_offers(product_id)
