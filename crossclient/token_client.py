"""
The `TokenClient` handles authentication and token refreshing. In normal use cases
this client is not directly used but automatically handled through the
[CrossClient][crossclient.cross_client.CrossClient].
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import BaseModel, Field, PrivateAttr, computed_field, model_validator


class Token(BaseModel):
    """Token represents the authentication token structure returned by the API. It
    includes the access token, refresh token, token type, creation timestamp, and
    expiration details."""

    access_token: str = Field(description="The access token for authentication.")
    refresh_token: str = Field(
        description="The refresh token for obtaining new access tokens."
    )
    token_type: str = Field(description="The type of the token.")
    created_at: datetime = Field(
        default=datetime.now(timezone.utc),
        description="The timestamp when the token was created.",
    )
    expires_in: int = Field(
        description="The duration in seconds until the access token expires."
    )
    refresh_expires_in: int = Field(
        description="The duration in seconds until the refresh token expires."
    )

    @property
    def is_expired(self) -> bool:
        """Check if the access token has expired.

        Returns:
            bool: True if the token has expired, False otherwise.
        """
        expiration_time = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.now(timezone.utc) >= expiration_time

    @property
    def is_refresh_expired(self) -> bool:
        """Check if the refresh token has expired.

        Returns:
            bool: True if the refresh token has expired, False otherwise.
        """
        refresh_expiration_time = self.created_at + timedelta(
            seconds=self.refresh_expires_in
        )
        return datetime.now(timezone.utc) >= refresh_expiration_time


class TokenClient(BaseModel):
    """The TokenClient handles authentication and token management for the API. It
    retrieves and refreshes access tokens as needed. For most use cases, a direct
    interaction with this client is not necessary, as the CrossClient will manage
    tokens automatically by incorporating the TokenClient internally."""

    username: str = Field(description="The username for authentication.")
    password: str = Field(description="The password for authentication.")
    base_url: str = Field(description="The base URL of the API.")
    transport: Any | None = Field(
        default=None,
        exclude=True,
        description="Optional custom transport for the HTTP client.",
    )
    _token: Token | None = PrivateAttr(default=None)
    _client: httpx.Client | None = PrivateAttr(default=None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url_auth(self) -> str:
        """URL of the authentication endpoint."""
        return f"{self.base_url}/login/access_token"  # pragma: no cover

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url_refresh(self) -> str:
        """URL of the token refresh endpoint."""
        return f"{self.base_url}/login/refresh_token"  # pragma: no cover

    @model_validator(mode="after")
    def _initialize_client_and_token(self) -> "TokenClient":
        self._client = httpx.Client(base_url=self.base_url, transport=self.transport)
        self._token = self._get_token()
        return self

    @property
    def token(self) -> Token:
        """Get the current token.

        Returns:
            Token: The current authentication token.
        """
        if self._token is None or self._token.is_expired:
            # Todo we could use refresh token here
            self._token = self._get_token()
        return self._token

    def _get_token(self) -> Token:
        """Retrieve a new access token using the refresh token.

        Returns:
            str: The new access token.
        """
        assert self._client is not None, "Client should be initialized"
        response = self._client.post(
            self.url_auth,
            data={"username": self.username, "password": self.password},
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to obtain access token: {response.text}")
        return Token.model_validate(response.json())
