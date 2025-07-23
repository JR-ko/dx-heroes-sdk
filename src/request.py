import json
from typing import Any, Dict, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def get_headers(token: str) -> Dict[str, str]:
    headers = {"Bearer": token, "accept": "application/json"}
    return headers


@retry(
    retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ConnectError)),
    wait=wait_exponential(),
    stop=stop_after_attempt(5),
)
async def perform_request(
    url: str, method: str, token, data: Optional[Dict[str, Any]] = None
) -> Any:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=get_headers(token), json=data
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )
        raise
    except httpx.RequestError as e:
        logger.error(f"error occurred while requesting {e.request.url}")
        raise
    except json.JSONDecodeError:
        logger.error(f"failed to decode JSON from response")
        raise
