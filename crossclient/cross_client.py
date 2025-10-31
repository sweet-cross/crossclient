"""
The `CrossClient` is main client to interact with CROSS API it provides different
methods that formulate the request to the API and return the response. It is
initialized using the user name and password and automatically handles
authentication.

The standard usage is:

``` py title="Example: Initializing the CrossClient"
from crossclient import CrossClient

client = CrossClient(
    username="me",
    password="my_password",
)
```
"""

from typing import Any

import httpx

from pydantic import BaseModel, Field, model_validator
from .token_client import TokenClient


class CrossClient(BaseModel):
    """CrossClient is the basic client to interact with the SweetCross API. It
    provides basic request methods to interact with the API endpoints. It also
    handles authentication via tokens based on the underlying TokenClient."""

    username: str = Field(description="The username for authentication.")
    password: str = Field(description="The password for authentication.")
    base_url: str = Field(
        default="https://sweetcross.link/api/v1",
        description="The base URL of the SweetCross API.",
    )
    transport: Any | None = Field(
        default=None,
        exclude=True,
        description="Optional custom transport for the HTTP client.",
    )
    _client: httpx.Client | None = None
    _token_client: TokenClient | None = None

    @model_validator(mode="after")
    def _initialized_clients(self) -> "CrossClient":
        """Validator to retrieve the token after model initialization and
        initialize the HTTP client."""
        self._token_client = TokenClient(
            username=self.username,
            password=self.password,
            base_url=self.base_url,
            transport=self.transport,
        )
        self._client = httpx.Client(base_url=self.base_url, transport=self.transport)
        return self

    def _request(
        self, method: str, endpoint: str, headers: dict | None = None, **kwargs
    ) -> httpx.Response:
        """Formulate an API requests given the name of the endpoint and the
        request method

        Args:
            method (str): The HTTP method to use (e.g., "GET", "POST").
            endpoint (str): The API endpoint to send the request to.
            headers (dict | None): Headers to include in the request.
            **kwargs: Additional arguments to pass to the request method.

        Returns:
            httpx.Response: The response from the API.
        """
        assert self._token_client is not None, "TokenClient should be initialized"
        assert self._client is not None, "Client should be initialized"
        if headers is None:
            headers = {}
        headers["Authorization"] = (
            f"{self._token_client.token.token_type} {self._token_client.token.access_token}"
        )
        response = self._client.request(method, endpoint, headers=headers, **kwargs)
        return response

    def post(
        self, endpoint: str, json: dict | None = None, **kwargs: dict
    ) -> httpx.Response:
        """Send a POST request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint to send the request to.
            json (dict | None): The JSON payload to include in the request body.
            **kwargs: Additional arguments to pass to the request method.
        Returns:
            httpx.Response: The response from the API.
        """
        # take care of file handles if any
        file_handles_to_close = []
        if "files" in kwargs:
            for _, file_tuple in kwargs["files"].items():
                # file_tuple is (filename, file_handle, mimetype)
                file_handle = file_tuple[1]
                if hasattr(file_handle, "close"):
                    file_handles_to_close.append(file_handle)
        try:
            # Pass control to the request method for authentication and execution
            return self._request("POST", endpoint, json=json, **kwargs)
        finally:
            # in anyways close the file handles after request completion
            for handle in file_handles_to_close:
                handle.close()

    def get(self, endpoint: str, **kwargs: dict) -> httpx.Response:
        """Send a GET request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint to send the request to.
            **kwargs: Additional arguments to pass to the request method.

        Returns:
            httpx.Response: The response from the API.
        """
        return self._request("GET", endpoint, **kwargs)
