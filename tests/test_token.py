from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import ValidationError

from crossclient.token_client import Token, TokenClient

token_data = {
    "access_token": "abc123",
    "refresh_token": "def456",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 7200,
}


def mock_api_handler(request: httpx.Request) -> httpx.Response:
    """
    This is our mock "server". It inspects the request
    and returns the appropriate fake response.
    """
    match (request.method, request.url.path):
        case ("POST", "/login/access_token"):
            if request.content == b"username=testuser&password=testpass":
                return httpx.Response(status_code=200, json=token_data)
            else:
                return httpx.Response(
                    status_code=401, json={"error": "Invalid credentials"}
                )

    # Fallback for any other unhandled request
    return httpx.Response(status_code=500, json={"error": "Unhandled mock request"})


class TestTokenExpiry:
    def test_is_expired_true(self):
        token = Token.model_validate(token_data)
        assert not token.is_expired

    def test_is_expired_false(self):
        token = Token.model_validate(token_data)
        token.created_at = datetime.now(timezone.utc) - timedelta(
            seconds=token.expires_in + 10
        )
        assert token.is_expired

    def test_refresh_is_expired_true(self):
        token = Token.model_validate(token_data)
        assert not token.is_refresh_expired

    def test_refresh_is_expired_false(self):
        token = Token.model_validate(token_data)
        token.created_at = datetime.now(timezone.utc) - timedelta(
            seconds=token.refresh_expires_in + 10
        )
        assert token.is_refresh_expired


class TestTokenClient:
    def test_get_token_successful(self):
        transport = httpx.MockTransport(mock_api_handler)
        client = TokenClient(
            username="testuser",
            password="testpass",
            base_url="http://testserver",
            transport=transport,
        )
        assert client.token.access_token == token_data["access_token"]

    def test_get_token_no_access(self):
        transport = httpx.MockTransport(mock_api_handler)
        with pytest.raises(ValidationError):
            TokenClient(
                username="testuser",
                password="nope",
                base_url="http://testserver",
                transport=transport,
            )

    def test_token_refresh(self):
        transport = httpx.MockTransport(mock_api_handler)
        client = TokenClient(
            username="testuser",
            password="testpass",
            base_url="http://testserver",
            transport=transport,
        )
        my_token = client.token
        # render the existing token invalid
        my_token.created_at = datetime.now(timezone.utc) - timedelta(
            seconds=my_token.expires_in + 10
        )
        my_token.access_token = "fake"
        assert my_token.is_expired

        # call the token again should trigger refresh
        new_token = client.token
        assert new_token.access_token == token_data["access_token"]
        assert not new_token.is_expired
