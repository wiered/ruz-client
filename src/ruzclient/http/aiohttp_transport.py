from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

from ..errors import RuzClientError
from .transport import TransportResponse


class AiohttpTransport:
    """Реализация `AsyncHttpTransport` на базе `aiohttp.ClientSession`."""

    def __init__(
        self,
        *,
        timeout_s: float = 30.0,
        session: Optional[Any] = None,
    ) -> None:
        try:
            import aiohttp  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "aiohttp is required for AiohttpTransport. Install with `pip install aiohttp`."
            ) from e

        self._aiohttp = aiohttp
        self._own_session = session is None
        if session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout_s),
            )
        else:
            self._session = session

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
        timeout = self._aiohttp.ClientTimeout(total=timeout_s)
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
            ) as resp:
                text = await resp.text()
                hdrs = {k: v for k, v in resp.headers.items()}
                return TransportResponse(
                    status_code=resp.status,
                    headers=hdrs,
                    url=str(resp.url),
                    body_text=text,
                )
        except self._aiohttp.ClientError as e:
            raise RuzClientError(f"Network error: {e}") from e
        except asyncio.TimeoutError as e:
            raise RuzClientError(f"Network error: {e}") from e

    async def aclose(self) -> None:
        if self._own_session:
            await self._session.close()
