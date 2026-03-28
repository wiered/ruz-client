from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

from ..errors import RuzClientError
from .transport import TransportResponse


class HttpxTransport:
    """Реализация `AsyncHttpTransport` на базе `httpx.AsyncClient`."""

    def __init__(
        self,
        *,
        timeout_s: float = 30.0,
        client: Optional[Any] = None,
    ) -> None:
        try:
            import httpx  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "httpx is required for HttpxTransport. Install with `pip install httpx` "
                "or `pip install ruz-client[httpx]`."
            ) from e

        self._httpx = httpx
        self._own_client = client is None
        if client is None:
            self._client = httpx.AsyncClient(timeout=timeout_s)
        else:
            self._client = client

    async def send(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout_s: float = 30.0,
    ) -> TransportResponse:
        try:
            r = await self._client.request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout_s,
            )
        except self._httpx.HTTPError as e:
            raise RuzClientError(f"Network error: {e}") from e
        except asyncio.TimeoutError as e:
            raise RuzClientError(f"Network error: {e}") from e

        body_text = r.text
        hdrs = dict(r.headers)
        return TransportResponse(
            status_code=r.status_code,
            headers=hdrs,
            url=str(r.url),
            body_text=body_text,
        )

    async def aclose(self) -> None:
        if self._own_client:
            await self._client.aclose()
