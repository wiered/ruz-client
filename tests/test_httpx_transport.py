from __future__ import annotations

import json

import httpx
import pytest

pytest.importorskip("httpx")

from ruzclient.errors import RuzClientError
from ruzclient.http.httpx_transport import HttpxTransport
from ruzclient.http.transport import TransportResponse


@pytest.mark.asyncio
async def test_httpx_transport_maps_response_to_transport_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(
            200,
            json={"a": 1},
            headers={"Content-Type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        t = HttpxTransport(client=client)
        r = await t.send("GET", "http://example.test/x", timeout_s=5.0)

    assert isinstance(r, TransportResponse)
    assert r.status_code == 200
    assert json.loads(r.body_text) == {"a": 1}


@pytest.mark.asyncio
async def test_httpx_transport_http_error_wraps() -> None:
    from unittest.mock import AsyncMock, MagicMock

    hc = MagicMock()
    hc.request = AsyncMock(
        side_effect=httpx.ConnectError(
            "refused", request=httpx.Request("GET", "http://example.test")
        )
    )
    t = HttpxTransport(client=hc)
    with pytest.raises(RuzClientError, match="Network error"):
        await t.send("GET", "http://example.test/x", timeout_s=1.0)
