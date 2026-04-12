from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

__all__ = ["TransportResponse", "AsyncHttpTransport"]


@dataclass(frozen=True)
class TransportResponse:
    """
    Нейтральный ответ HTTP: тело уже прочитано в виде текста.

    Заголовки — обычный mapping; поиск `Content-Type` в `RuzClient` делается
    без учёта регистра.
    """

    status_code: int
    headers: Mapping[str, str]
    url: str
    body_text: str


@runtime_checkable
class AsyncHttpTransport(Protocol):
    """Плавающий HTTP-слой: одна отправка запроса и закрытие ресурсов."""

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
    ) -> TransportResponse: ...

    async def aclose(self) -> None: ...
