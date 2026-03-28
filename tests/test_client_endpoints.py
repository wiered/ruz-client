from __future__ import annotations

import json

import pytest

from tests.fake_transport import FakeTransport
from ruzclient.client import ClientConfig, RuzClient
from ruzclient.errors import RuzAuthError, RuzHttpError
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"


def _make_client(fake: FakeTransport, **kwargs: object) -> RuzClient:
    cfg = ClientConfig(base_url=BASE, **kwargs)
    return RuzClient(cfg, transport=fake)


@pytest.mark.asyncio
async def test_healthz_returns_json() -> None:
    body = json.dumps({"status": "ok"})
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/healthz",
                body_text=body,
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.healthz()
    assert out == {"status": "ok"}


@pytest.mark.asyncio
async def test_healthz_returns_text_when_not_json_content_type() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "text/plain"},
                url=f"{BASE}/healthz",
                body_text="plain",
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.healthz()
    assert out == "plain"


@pytest.mark.asyncio
async def test_healthz_204_returns_none() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=204,
                headers={},
                url=f"{BASE}/healthz",
                body_text="",
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.healthz()
    assert out is None


@pytest.mark.asyncio
async def test_healthz_strips_api_suffix_from_base_url() -> None:
    """`BASE_URL` may end with `/api`; пути клиента всё равно `api/...` без дубля."""
    base_with_api = "http://127.0.0.1:2201/api"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url="http://127.0.0.1:2201/healthz",
                body_text=json.dumps({"ok": True}),
            )
        ]
    )
    cfg = ClientConfig(base_url=base_with_api)
    async with RuzClient(cfg, transport=fake) as client:
        out = await client.healthz()
    assert out == {"ok": True}
    assert fake.calls[0]["url"] == "http://127.0.0.1:2201/healthz"


@pytest.mark.asyncio
async def test_public_ok_without_token(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/public",
                body_text=json.dumps({"open": True}),
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.public()
    assert out == {"open": True}


@pytest.mark.asyncio
async def test_public_sends_x_api_key_from_env(env_api_key: str) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/public",
                body_text=json.dumps({"ok": True}),
            )
        ]
    )
    async with _make_client(fake) as client:
        await client.public()
    assert fake.calls[0]["headers"].get("X-API-Key") == env_api_key


@pytest.mark.asyncio
async def test_public_sends_x_api_key_from_config(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/public",
                body_text=json.dumps({"ok": True}),
            )
        ]
    )
    cfg = ClientConfig(base_url=BASE, api_key="cfg-key-123")
    async with RuzClient(cfg, transport=fake) as client:
        await client.public()
    assert fake.calls[0]["headers"].get("X-API-Key") == "cfg-key-123"


@pytest.mark.asyncio
async def test_protected_ok_with_config_api_key(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/protected",
                body_text=json.dumps({"data": 1}),
            )
        ]
    )
    cfg = ClientConfig(base_url=BASE, api_key="secret")
    async with RuzClient(cfg, transport=fake) as client:
        out = await client.protected()
    assert out == {"data": 1}


@pytest.mark.asyncio
async def test_protected_ok_with_explicit_api_key_arg(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/protected",
                body_text=json.dumps({"ok": True}),
            )
        ]
    )
    async with _make_client(fake) as client:
        await client.protected(api_key="one-off-key")
    assert fake.calls[0]["headers"].get("X-API-Key") == "one-off-key"


@pytest.mark.asyncio
async def test_protected_401_raises_auth_error(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=401,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/protected",
                body_text=json.dumps({"detail": "nope"}),
            )
        ]
    )
    async with _make_client(fake) as client:
        with pytest.raises(RuzAuthError) as ei:
            await client.protected()
    assert "401" in str(ei.value)


@pytest.mark.asyncio
async def test_protected_403_raises_auth_error(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=403,
                headers={},
                url=f"{BASE}/protected",
                body_text="forbidden",
            )
        ]
    )
    async with _make_client(fake) as client:
        with pytest.raises(RuzAuthError):
            await client.protected()


@pytest.mark.asyncio
async def test_protected_500_raises_http_error(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=500,
                headers={},
                url=f"{BASE}/protected",
                body_text="srv err",
            )
        ]
    )
    cfg = ClientConfig(base_url=BASE, api_key="x")
    async with RuzClient(cfg, transport=fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.protected()
    assert ei.value.status_code == 500


@pytest.mark.asyncio
async def test_public_404_raises_http_error(no_token) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=404,
                headers={},
                url=f"{BASE}/public",
                body_text="missing",
            )
        ]
    )
    async with _make_client(fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.public()
    assert ei.value.status_code == 404
