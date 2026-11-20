from types import TracebackType
from typing import Any

import httpx

from backend.app.config import get_setting


class AdzunaClient:
    """Asynchronous client for searching jobs through the Adzuna API."""

    # Load Adzuna credentials and prepare a reusable asynchronous HTTP client.
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        setting = get_setting()
        self._base_url = setting.adzuna_base_url.rstrip("/")
        self._app_id = setting.adzuna_id
        self._app_key = setting.adzuna_api_key
        self._client = client if client is not None else httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None

    # Request one page of jobs with optional keyword and location filters.
    async def fetch_jobs(
        self,
        country_code: str,
        *,
        page: int = 1,
        results_per_page: int = 20,
        what: str | None = None,
        where: str | None = None,
    ) -> list[dict[str, Any]]:
        if not country_code.isalpha() or len(country_code) != 2:
            raise ValueError("country_code must be a two-letter country code.")
        if page < 1:
            raise ValueError("page must be a positive integer.")
        if results_per_page < 1:
            raise ValueError("results_per_page must be a positive integer.")

        params: dict[str, str | int] = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        if what:
            params["what"] = what
        if where:
            params["where"] = where

        url = f"{self._base_url}/{country_code.lower()}/search/{page}"
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()["results"]

    # Close only internally-created clients; injected clients belong to their caller.
    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # Enable use with `async with` so the client can be cleaned up reliably.
    async def __aenter__(self) -> "AdzunaClient":
        return self

    # Release the owned HTTP connection pool when leaving an async context.
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()