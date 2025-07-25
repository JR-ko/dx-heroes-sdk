from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.models import Offer, Product, ProductRegistered


class TestProduct:
    def test_product_creation_valid(self):
        product_id = uuid4()
        product = Product(
            id=product_id, name="Test Product", description="A test product description"
        )

        assert product.id == product_id
        assert product.name == "Test Product"
        assert product.description == "A test product description"

    def test_product_creation_missing_fields(self):
        with pytest.raises(ValidationError):
            Product(name="Test Product")

    def test_product_creation_invalid_uuid(self):
        with pytest.raises(ValidationError):
            Product(
                id="not-a-uuid",
                name="Test Product",
                description="A test product description",
            )

    def test_product_model_dump(self):
        product_id = uuid4()
        product = Product(
            id=product_id, name="Test Product", description="A test product description"
        )

        dumped = product.model_dump(mode="json")

        assert dumped["id"] == str(product_id)
        assert dumped["name"] == "Test Product"
        assert dumped["description"] == "A test product description"


class TestProductRegistered:
    def test_product_registered_creation_valid(self):
        product_id = uuid4()
        product_registered = ProductRegistered(id=product_id)

        assert product_registered.id == product_id

    def test_product_registered_creation_missing_id(self):
        with pytest.raises(ValidationError):
            ProductRegistered()

    def test_product_registered_creation_invalid_uuid(self):
        with pytest.raises(ValidationError):
            ProductRegistered(id="not-a-uuid")

    def test_product_registered_model_dump(self):
        product_id = uuid4()
        product_registered = ProductRegistered(id=product_id)

        dumped = product_registered.model_dump(mode="json")

        assert dumped["id"] == str(product_id)


class TestOffer:
    def test_offer_creation_valid(self):
        offer_id = uuid4()
        offer = Offer(id=offer_id, price=100, items_in_stock=10)

        assert offer.id == offer_id
        assert offer.price == 100
        assert offer.items_in_stock == 10

    def test_offer_creation_missing_fields(self):
        with pytest.raises(ValidationError):
            Offer(id=uuid4(), price=100)

    def test_offer_creation_invalid_uuid(self):
        with pytest.raises(ValidationError):
            Offer(id="not-a-uuid", price=100, items_in_stock=10)

    def test_offer_creation_invalid_price_type(self):
        with pytest.raises(ValidationError):
            Offer(id=uuid4(), price="not-an-int", items_in_stock=10)

    def test_offer_creation_invalid_stock_type(self):
        with pytest.raises(ValidationError):
            Offer(id=uuid4(), price=100, items_in_stock="not-an-int")

    def test_offer_model_dump(self):
        offer_id = uuid4()
        offer = Offer(id=offer_id, price=100, items_in_stock=10)

        dumped = offer.model_dump(mode="json")

        assert dumped["id"] == str(offer_id)
        assert dumped["price"] == 100
        assert dumped["items_in_stock"] == 10
