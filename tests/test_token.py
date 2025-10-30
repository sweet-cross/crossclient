from crossclient.token_client import Token
from datetime import datetime, timezone, timedelta

token_data = {
    "access_token": "abc123",
    "refresh_token": "def456",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 7200,
}


class TestTokenValidation:
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
