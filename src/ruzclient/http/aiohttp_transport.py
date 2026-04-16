from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..errors import RuzClientError
from .transport import TransportResponse


class AiohttpTransport:
    """Реализация `AsyncHttpTransport` на базе `aiohttp.ClientSession`."""

    def __init__(
        self,
        *,
        timeout_s: float = 30.0,
        session: Any | None = None,
    ) -> None:
        try:
            import aiohttp  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "aiohttp is required for AiohttpTransport. "
                "Install with `pip install aiohttp`."
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
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: Mapping[str, str] | None = None,
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
        except TimeoutError as e:
            raise RuzClientError(f"Network error: {e}") from e

    async def aclose(self) -> None:
        if self._own_session:
            await self._session.close()
