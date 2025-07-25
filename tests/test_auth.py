import json
import os
from pathlib import Path
from time import time
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
from uuid import uuid4

import httpx
import jwt
import pytest

from src.auth import TokenManager


@pytest.fixture
def token_manager():
    return TokenManager("test_refresh_token", "https://test.api.com")


@pytest.fixture
def valid_jwt_token():
    expires_timestamp = int(time()) + 3600
    return jwt.encode({"expires": expires_timestamp}, "secret", algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    expires_timestamp = int(time()) - 3600
    return jwt.encode({"expires": expires_timestamp}, "secret", algorithm="HS256")


class TestTokenManager:
    def test_init(self, token_manager):
        assert token_manager.refresh_token == "test_refresh_token"
        assert token_manager.base_url == "https://test.api.com"
        assert token_manager.token_file == Path(
            os.path.expanduser("./.dx_heroes_token.json")
        )

    def test_load_access_token_from_file_success(self, token_manager):
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.read_text") as mock_read_text,
        ):
            mock_exists.return_value = True
            mock_read_text.return_value = '{"access_token": "test_token"}'
            token = token_manager.load_access_token_from_file()
            assert token == "test_token"

    def test_load_access_token_from_file_not_exists(self, token_manager):
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            token = token_manager.load_access_token_from_file()
            assert token is None

    def test_load_access_token_from_file_json_error(self, token_manager):
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.read_text") as mock_read_text,
        ):
            mock_exists.return_value = True
            mock_read_text.return_value = "invalid json"
            token = token_manager.load_access_token_from_file()
            assert token is None

    def test_save_access_token_to_file_success(self, token_manager):
        with patch("pathlib.Path.write_text") as mock_write:
            token_manager.save_access_token_to_file("test_token")
            mock_write.assert_called_once_with('{"access_token": "test_token"}')

    def test_save_access_token_to_file_os_error(self, token_manager):
        with patch("pathlib.Path.write_text") as mock_write:
            mock_write.side_effect = OSError("Permission denied")
            with pytest.raises(OSError):
                token_manager.save_access_token_to_file("test_token")

    def test_is_token_expired_valid_token(self, token_manager, valid_jwt_token):
        assert not token_manager.is_token_expired(valid_jwt_token)

    def test_is_token_expired_expired_token(self, token_manager, expired_jwt_token):
        assert token_manager.is_token_expired(expired_jwt_token)

    @pytest.mark.asyncio
    async def test_authenticate_success(self, token_manager):
        with patch("src.auth.perform_request") as mock_perform_request:
            mock_perform_request.return_value = {"access_token": "new_access_token"}
            with patch.object(token_manager, "save_access_token_to_file") as mock_save:
                token = await token_manager.authenticate()
                mock_perform_request.assert_called_once_with(
                    "https://test.api.com/auth", "POST", "test_refresh_token"
                )
                mock_save.assert_called_once_with("new_access_token")
                assert token == "new_access_token"
                assert token_manager.access_token == "new_access_token"

    @pytest.mark.asyncio
    async def test_get_access_token_no_token(self, token_manager):
        token_manager.access_token = None
        with patch.object(token_manager, "authenticate") as mock_auth:
            mock_auth.return_value = "new_token"
            token = await token_manager.get_access_token()
            mock_auth.assert_called_once()
            assert token == "new_token"

    @pytest.mark.asyncio
    async def test_get_access_token_expired_token(
        self, token_manager, expired_jwt_token
    ):
        token_manager.access_token = expired_jwt_token
        with patch.object(token_manager, "authenticate") as mock_auth:
            mock_auth.return_value = "new_token"
            token = await token_manager.get_access_token()
            mock_auth.assert_called_once()
            assert token == "new_token"

    @pytest.mark.asyncio
    async def test_get_access_token_valid_token(self, token_manager, valid_jwt_token):
        token_manager.access_token = valid_jwt_token
        with patch.object(token_manager, "authenticate") as mock_auth:
            token = await token_manager.get_access_token()
            mock_auth.assert_not_called()
            assert token == valid_jwt_token

    @pytest.mark.asyncio
    async def test_execute_authenticated_request_success(self, token_manager):
        token_manager.access_token = "valid_token"
        with (
            patch("src.auth.perform_request") as mock_perform_request,
            patch.object(token_manager, "get_access_token") as mock_get_access_token,
        ):
            mock_get_access_token.return_value = "valid_token"
            mock_perform_request.return_value = {"result": "success"}

            result = await token_manager.execute_authenticated_request(
                "https://test.api.com/endpoint", "GET", {"data": "test"}
            )

            mock_perform_request.assert_called_once_with(
                "https://test.api.com/endpoint", "GET", "valid_token", {"data": "test"}
            )
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_execute_authenticated_request_401_retry(self, token_manager):
        response_mock = MagicMock()
        response_mock.status_code = 401
        error_401 = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=response_mock
        )
        with patch("src.auth.perform_request") as mock_perform_request:
            mock_perform_request.side_effect = [error_401, {"result": "success"}]

            with (
                patch.object(
                    token_manager, "get_access_token"
                ) as mock_get_access_token,
                patch.object(token_manager, "authenticate") as mock_authenticate,
            ):
                mock_get_access_token.return_value = "old_token"
                mock_authenticate.return_value = "new_token"
                result = await token_manager.execute_authenticated_request(
                    "https://test.api.com/endpoint", "GET"
                )

                assert mock_perform_request.call_count == 2
                assert result == {"result": "success"}
