import asyncio
import os
from uuid import uuid4

from dotenv import load_dotenv
from loguru import logger

from src.client import ProductClient
from src.models import Product

load_dotenv()


async def main():
    client = ProductClient(refresh_token=os.getenv("REFRESH_TOKEN"))

    product = Product(
        id=uuid4(),
        name="Premium Almond Butter",
        description="Made from high-quality Spanish almonds",
    )

    registered_product = await client.register_product(product)
    logger.info(f"registered product ID: {registered_product.id}")

    offers = await client.get_product_offers(registered_product.id)
    logger.info(f"product offers: {offers}")


asyncio.run(main())
