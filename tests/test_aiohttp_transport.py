from __future__ import annotations

import json

import pytest
from aioresponses import aioresponses

from ruzclient.http.aiohttp_transport import AiohttpTransport
from ruzclient.http.transport import TransportResponse


@pytest.mark.asyncio
async def test_aiohttp_transport_maps_response_to_transport_response() -> None:
    with aioresponses() as m:
        m.get(
            "http://127.0.0.1:2201/x",
            body=json.dumps({"a": 1}),
            status=200,
            headers={"Content-Type": "application/json"},
        )
        t = AiohttpTransport(timeout_s=5.0)
        try:
            r = await t.send("GET", "http://127.0.0.1:2201/x", timeout_s=5.0)
        finally:
            await t.aclose()

    assert isinstance(r, TransportResponse)
    assert r.status_code == 200
    assert json.loads(r.body_text) == {"a": 1}
    assert "application/json" in r.headers.get("Content-Type", "").lower()


@pytest.mark.asyncio
async def test_aiohttp_transport_client_error_wraps() -> None:
    """Ошибки aiohttp при запросе переводятся в `RuzClientError`."""
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    import aiohttp

    from ruzclient.errors import RuzClientError

    @asynccontextmanager
    async def _failing_request(*_a: object, **_kw: object):
        raise aiohttp.ClientConnectionError("connection refused")
        yield  # pragma: no cover

    session = MagicMock()
    session.request = lambda *a, **kw: _failing_request()
    t = AiohttpTransport(session=session)
    with pytest.raises(RuzClientError, match="Network error"):
        await t.send("GET", "http://example.test/x", timeout_s=1.0)
