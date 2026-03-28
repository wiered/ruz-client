from __future__ import annotations

from typing import TYPE_CHECKING

from .aiohttp_transport import AiohttpTransport
from .transport import AsyncHttpTransport, TransportResponse

__all__ = [
    "AiohttpTransport",
    "AsyncHttpTransport",
    "HttpxTransport",
    "TransportResponse",
]


def __getattr__(name: str):
    if name == "HttpxTransport":
        from .httpx_transport import HttpxTransport

        return HttpxTransport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .httpx_transport import HttpxTransport as HttpxTransport
