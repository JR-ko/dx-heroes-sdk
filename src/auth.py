import json
import os
from pathlib import Path
from time import time
from typing import Any, Dict, Optional

import httpx
import jwt
from loguru import logger

from .request import perform_request


class TokenManager:
    def __init__(self, refresh_token: str, base_url: str) -> None:
        self.refresh_token = refresh_token
        self.base_url = base_url
        self.token_file = Path(os.path.expanduser("./.dx_heroes_token.json"))
        self.access_token: Optional[str] = self.load_access_token_from_file()

    def save_access_token_to_file(self, token: str) -> None:
        try:
            self.token_file.write_text(json.dumps({"access_token": token}))
        except OSError as e:
            logger.error(f"error saving token to file: {e}")
            raise

    def load_access_token_from_file(self) -> Optional[str]:
        if not self.token_file.exists():
            return None
        try:
            data = json.loads(self.token_file.read_text())
            return data.get("access_token")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"error loading token from file: {e}")
            return None

    async def authenticate(self) -> str:
        token_data = await perform_request(
            f"{self.base_url}/auth", "POST", self.refresh_token
        )
        access_token = token_data.get("access_token")
        self.access_token = access_token
        self.save_access_token_to_file(access_token)
        return access_token

    def is_token_expired(self, token: str) -> bool:
        try:
            token_data = jwt.decode(token, options={"verify_signature": False})
            token_exp_timestamp = token_data.get("expires", 0)
            current_timestamp = int(time())
            return token_exp_timestamp < current_timestamp
        except Exception as e:
            logger.error(f"error decoding JWT: {e}")
            return True

    async def get_access_token(self) -> str:
        if not self.access_token or self.is_token_expired(self.access_token):
            logger.info("token not saved in file or expired, getting new token")
            return await self.authenticate()
        logger.info("using saved token")
        return self.access_token

    async def execute_authenticated_request(
        self, url: str, method: str, data: Optional[Dict[str, Any]] = None
    ) -> Any:
        try:
            access_token = await self.get_access_token()
            return await perform_request(url, method, access_token, data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.info("trying auth once again")
                access_token = await self.authenticate()
                return await perform_request(url, method, access_token, data)
            raise
