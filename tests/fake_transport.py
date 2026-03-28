from __future__ import annotations

from typing import Any, Optional

from ruzclient.http.transport import TransportResponse


class FakeTransport:
    """Тестовая реализация `AsyncHttpTransport`: заранее заданные ответы и журнал вызовов."""

    def __init__(self, responses: list[TransportResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def send(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[dict[str, str]] = None,
        timeout_s: float = 30.0,
    ) -> TransportResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "json": json,
                "data": data,
                "headers": dict(headers) if headers else {},
                "timeout_s": timeout_s,
            }
        )
        if not self._responses:
            raise RuntimeError("FakeTransport: no more canned responses")
        return self._responses.pop(0)

    async def aclose(self) -> None:
        pass
