# Python SDK for Offers API

This project contains a Python SDK for interacting with an external API to register products and retrieve product offers. It also includes a test suite to verify the application's functionality.

SDK includes following features:

- make asynchronous API calls to the external API using `httpx`
- handles JWT access token acquisition and refresh, including expiration validation and its storage for subsequent use.
- implements an exponential backoff retry mechanism for network errors.
- uses Pydantic for request body validation.

## Quickstart

### Prerequisites 

Ensure you have [Python3.12](https://www.python.org/downloads/) or higher and [uv](https://github.com/astral-sh/uv) package manager installed

### Installation & Setup

1. **Create and activate a virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate
    ```

2. **Install dependencies:**

    ```bash
    uv pip install -r pyproject.toml
    ```

3. **Create a `.env` file:** Create a `.env` file in the root directory and add your refresh token

    ```
    REFRESH_TOKEN=your_refresh_token
    ```

### Running the Application

To run the application, run this python:

```python
import asyncio
import os
from uuid import uuid4

from loguru import logger

from src.client import ProductClient
from src.models import Product

async def main():
    # initialize the client with your refresh token
    client = ProductClient(refresh_token="your_refresh_token_here")

    # create a product
    product = Product(
        id=uuid4(),
        name="Premium Almond Butter",
        description="Made from high-quality Spanish almonds",
    )

    # register the product
    registered_product = await client.register_product(product)
    logger.info(f"registered product ID: {registered_product.id}")

    # get offers for the product
    offers = await client.get_product_offers(registered_product.id)
    logger.info(f"product offers: {offers}")


asyncio.run(main())
```

## Testing the SDK

The SDK includes a comprehensive test suite covering all components with unit tests using pytest and async testing patterns. The test suite is organized into four main test modules in the `tests/` directory. Execute the full test suite:

```bash
pytest
```

## Examples

Simple example showing how to register a single product and retrieve its offers. Refresh token is retrieved from `.env` file

```python
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
    
    products = [
        Product(
            id=uuid4(),
            name="Premium Almond Butter",
            description="Made from high-quality Spanish almonds"
        ),
        Product(
            id=uuid4(),
            name="Organic Honey",
            description="Raw organic honey from local beekeepers"
        )
    ]
    
    for product in products:
        registered = await client.register_product(product)
        logger.info(f"registered: {product.name} (ID: {registered.id})")
        
        offers = await client.get_product_offers(registered.id)
        if offers:
            best_offer = min(offers, key=lambda x: x.price)
            logger.info(f"best offer price: {best_offer.price} ({best_offer.items_in_stock} in stock)")
        else:
            logger.info("no offers available")

asyncio.run(main())
```