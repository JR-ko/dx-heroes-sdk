import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.request import perform_request


class TestPerformRequest:
    base_url = "https://test.api.com"
    default_token = "test_token"
    default_headers = {"Bearer": default_token, "accept": "application/json"}
    success_response = {"result": "success"}
    raise_for_status = None

    @pytest.mark.asyncio
    async def test_perform_request_get_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response
        mock_response.raise_for_status.return_value = self.raise_for_status

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await perform_request(
                f"{self.base_url}/endpoint", "GET", self.default_token
            )

            mock_client.request.assert_called_once_with(
                "GET",
                f"{self.base_url}/endpoint",
                headers=self.default_headers,
                json=None,
            )
            assert result == self.success_response

    @pytest.mark.asyncio
    async def test_perform_request_post_with_data(self):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "created": True}
        mock_response.raise_for_status.return_value = self.raise_for_status

        test_data = {"name": "test", "value": 42}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            result = await perform_request(
                f"{self.base_url}/create", "POST", self.default_token, test_data
            )

            mock_client.request.assert_called_once_with(
                "POST",
                f"{self.base_url}/create",
                headers=self.default_headers,
                json=test_data,
            )
            assert result == {"id": "123", "created": True}

    @pytest.mark.asyncio
    async def test_perform_request_http_status_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        http_error = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_response.raise_for_status.side_effect = http_error

            with pytest.raises(httpx.HTTPStatusError):
                await perform_request(
                    f"{self.base_url}/endpoint", "GET", self.default_token
                )

    @pytest.mark.asyncio
    async def test_perform_request_request_error(self):
        mock_request = MagicMock()
        mock_request.url = "https://test.api.com/endpoint"
        request_error = httpx.RequestError("Request failed", request=mock_request)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = request_error

            with pytest.raises(httpx.RequestError):
                await perform_request(
                    f"{self.base_url}/endpoint", "GET", self.default_token
                )

    @pytest.mark.asyncio
    async def test_perform_request_max_retries_exceeded(self):
        mock_request = MagicMock()
        mock_request.url = "https://test.api.com/endpoint"
        timeout_error = httpx.ConnectTimeout("Connection timeout", request=mock_request)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.request.side_effect = timeout_error

            with pytest.raises(Exception):
                await perform_request(
                    f"{self.base_url}/endpoint", "GET", self.default_token
                )

            assert mock_client.request.call_count == 5
