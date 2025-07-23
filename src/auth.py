from time import time
from typing import Optional

import jwt
from loguru import logger

from .request import perform_request


class TokenManager:
    def __init__(self, refresh_token: str, base_url: str) -> None:
        self.refresh_token = refresh_token
        self.base_url = base_url
        self.access_token: Optional[str] = None

    async def authenticate(self) -> str:
        token_data = await perform_request(
            f"{self.base_url}/auth", "POST", self.refresh_token
        )
        access_token = token_data.get("access_token")
        logger.info(f"access token: {access_token}")
        self.access_token = access_token
        return access_token

    def is_token_expired(self, token: str) -> bool:
        try:
            token_data = jwt.decode(token, options={"verify_signature": False})
            token_exp_timestamp = token_data.get("expires", 0)
            current_timestamp = int(time())
            return token_exp_timestamp < current_timestamp
        except Exception as e:
            logger.error(f"error decoding JWT: {e}")
            return False

    async def get_access_token(self) -> str:
        if not self.access_token:
            logger.info("token not cached, generated new")
            return await self.authenticate()
        if self.is_token_expired(self.access_token):
            logger.info("token expired, refreshing")
            return await self.authenticate()
        logger.info("token still in cache")
        return self.access_token
