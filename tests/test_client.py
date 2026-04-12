from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from ruzclient.client import (
    ClientConfig,
    RuzClient,
    _content_type_lower,
    _normalize_base_url,
)
from ruzclient.errors import RuzHttpError
from ruzclient.http.endpoints.disciplines import DisciplinesEndpoints
from ruzclient.http.endpoints.groups import GroupsEndpoints
from ruzclient.http.endpoints.lecturers import LecturersEndpoints
from ruzclient.http.endpoints.schedule import ScheduleEndpoints
from ruzclient.http.endpoints.search import SearchEndpoints
from ruzclient.http.endpoints.users import UsersEndpoints
from ruzclient.http.transport import TransportResponse
from tests.fake_transport import FakeTransport

BASE = "http://127.0.0.1:2201"


def _make_client(fake: FakeTransport, **kwargs: object) -> RuzClient:
    cfg = ClientConfig(base_url=BASE, **kwargs)
    return RuzClient(cfg, transport=fake)


# --- _normalize_base_url ---


def test_normalize_base_url_adds_scheme_and_default_port() -> None:
    assert _normalize_base_url("127.0.0.1") == "http://127.0.0.1:2201"


def test_normalize_base_url_host_with_path_gets_default_port() -> None:
    assert _normalize_base_url("127.0.0.1/api/v1") == "http://127.0.0.1:2201/api/v1"


def test_normalize_base_url_preserves_explicit_port_with_path_not_only_api() -> None:
    """Путь не заканчивается на `/api` целиком — суффикс не срезается."""
    assert _normalize_base_url("127.0.0.1:8080/v1/x") == "http://127.0.0.1:8080/v1/x"


def test_normalize_base_url_strips_whitespace() -> None:
    assert _normalize_base_url("  http://x:1/y/  ") == "http://x:1/y"


def test_normalize_base_url_https_unchanged() -> None:
    assert _normalize_base_url("https://api.example.com:443/x") == (
        "https://api.example.com:443/x"
    )


def test_normalize_base_url_strips_trailing_api_suffix() -> None:
    assert _normalize_base_url("http://127.0.0.1:2201/api") == "http://127.0.0.1:2201"


# --- _content_type_lower ---


def test_content_type_lower_missing_returns_empty() -> None:
    assert _content_type_lower({}) == ""


def test_content_type_lower_header_name_case_insensitive() -> None:
    assert _content_type_lower({"CoNtEnT-TyPe": "Application/JSON"}) == (
        "application/json"
    )


# --- RuzClient construction ---


def test_ruz_client_rejects_both_transport_and_client() -> None:
    fake = FakeTransport([])
    dummy_session = MagicMock()
    with pytest.raises(ValueError, match="only one of `transport` or `client`"):
        RuzClient(
            ClientConfig(base_url=BASE),
            transport=fake,
            client=dummy_session,
        )


def test_ruz_client_wraps_explicit_aiohttp_session() -> None:
    session = MagicMock()
    mock_transport = MagicMock()
    with patch(
        "ruzclient.client.AiohttpTransport", return_value=mock_transport
    ) as aiohttp_transport_cls:
        client = RuzClient(ClientConfig(base_url=BASE), client=session)
    aiohttp_transport_cls.assert_called_once_with(session=session)
    assert client._transport is mock_transport
    assert client._own_transport is False


# --- properties ---


def test_disciplines_property() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/x",
                body_text="{}",
            )
        ]
    )
    client = _make_client(fake)
    assert isinstance(client.disciplines, DisciplinesEndpoints)


def test_lecturers_property() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/x",
                body_text="{}",
            )
        ]
    )
    client = _make_client(fake)
    assert isinstance(client.lecturers, LecturersEndpoints)


def test_groups_schedule_search_users_properties() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/x",
                body_text="{}",
            )
        ]
    )
    client = _make_client(fake)
    assert isinstance(client.groups, GroupsEndpoints)
    assert isinstance(client.schedule, ScheduleEndpoints)
    assert isinstance(client.search, SearchEndpoints)
    assert isinstance(client.users, UsersEndpoints)


# --- aclose / owned transport ---


@pytest.mark.asyncio
async def test_aclose_closes_owned_transport() -> None:
    transport = AsyncMock()
    with patch("ruzclient.client.AiohttpTransport", return_value=transport):
        client = RuzClient(ClientConfig(base_url=BASE))
        assert client._own_transport is True
        await client.aclose()
    transport.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_aclose_skips_when_transport_not_owned() -> None:
    fake = FakeTransport([])
    client = _make_client(fake)
    await client.aclose()
    assert client._own_transport is False


@pytest.mark.asyncio
async def test_sequential_requests_reuse_fake_transport(no_token: None) -> None:
    """Несколько GET подряд: один клиент / один FakeTransport, ответы из очереди."""
    n = 5
    canned = [
        TransportResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            url=f"{BASE}/healthz",
            body_text=json.dumps({"i": i}),
        )
        for i in range(n)
    ]
    fake = FakeTransport(canned)
    async with _make_client(fake) as client:
        for i in range(n):
            out = await client.healthz()
            assert out == {"i": i}
    assert len(fake.calls) == n
    assert all(c["method"] == "GET" for c in fake.calls)


@pytest.mark.asyncio
async def test_ruz_client_sequential_requests_owned_session(no_token: None) -> None:
    """Повторное использование встроенного aiohttp-сессии: несколько запросов подряд."""
    url = f"{BASE}/public"
    with aioresponses() as m:
        m.get(
            url,
            body=json.dumps({"ok": True}),
            status=200,
            headers={"Content-Type": "application/json"},
            repeat=True,
        )
        client = RuzClient(ClientConfig(base_url=BASE))
        try:
            for _ in range(4):
                assert await client.public() == {"ok": True}
        finally:
            await client.aclose()


@pytest.mark.asyncio
async def test_ruz_client_concurrent_requests_owned_session(no_token: None) -> None:
    """Параллельные запросы через один клиент (reuse сессии под asyncio.gather)."""
    url = f"{BASE}/public"
    with aioresponses() as m:
        m.get(
            url,
            body=json.dumps({"ok": True}),
            status=200,
            headers={"Content-Type": "application/json"},
            repeat=True,
        )
        client = RuzClient(ClientConfig(base_url=BASE))
        try:
            results = await asyncio.gather(*(client.public() for _ in range(6)))
        finally:
            await client.aclose()
    assert results == [{"ok": True}] * 6


@pytest.mark.asyncio
async def test_ruz_client_aclose_twice_owned_does_not_raise(no_token: None) -> None:
    """Повторный `aclose()` не должен падать (как у `aiohttp.ClientSession.close()`)."""
    url = f"{BASE}/public"
    with aioresponses() as m:
        m.get(
            url,
            body="{}",
            status=200,
            headers={"Content-Type": "application/json"},
        )
        client = RuzClient(ClientConfig(base_url=BASE))
        await client.public()
        await client.aclose()
        await client.aclose()


@pytest.mark.asyncio
async def test_ruz_client_request_after_aclose_raises(no_token: None) -> None:
    """После `aclose()` сессия aiohttp закрыта — новый запрос даёт RuntimeError."""
    client = RuzClient(ClientConfig(base_url=BASE))
    await client.aclose()
    with pytest.raises(RuntimeError, match="Session is closed"):
        await client.public()


# --- _normalize_path ---


@pytest.mark.asyncio
async def test_get_empty_path_returns_base_url_only() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={},
                url=BASE,
                body_text="ok",
            )
        ]
    )
    async with _make_client(fake) as client:
        await client.get("")
    assert fake.calls[0]["url"] == BASE


@pytest.mark.asyncio
async def test_get_slash_only_path_returns_base_url_only() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={},
                url=BASE,
                body_text="ok",
            )
        ]
    )
    async with _make_client(fake) as client:
        await client.get("/")
    assert fake.calls[0]["url"] == BASE


@pytest.mark.asyncio
async def test_request_absolute_url_passes_through() -> None:
    url = "http://other.test/z"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={},
                url=url,
                body_text="x",
            )
        ]
    )
    async with _make_client(fake) as client:
        await client.get(url)
    assert fake.calls[0]["url"] == url


# --- _build_headers ---


@pytest.mark.asyncio
async def test_default_headers_and_per_request_headers_merge(
    no_token: None,
) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/public",
                body_text="{}",
            )
        ]
    )
    cfg = ClientConfig(
        base_url=BASE,
        default_headers={"X-A": "1", "X-B": "from-default"},
    )
    async with RuzClient(cfg, transport=fake) as client:
        await client.get(
            "public",
            headers={"X-B": "from-request", "X-C": "3"},
        )
    h = fake.calls[0]["headers"]
    assert h["X-A"] == "1"
    assert h["X-B"] == "from-request"
    assert h["X-C"] == "3"


@pytest.mark.asyncio
async def test_bearer_fallback_authorization_when_explicit_api_key_empty(
    no_token: None,
) -> None:
    """
    Пустая строка в `api_key` запроса не подставляет X-API-Key;
    остаётся фоллбэк Authorization для старой схемы.
    """
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/public",
                body_text="{}",
            )
        ]
    )
    cfg = ClientConfig(base_url=BASE, bearer_token="legacy-bearer")
    async with RuzClient(cfg, transport=fake) as client:
        await client.public(api_key="")
    h = fake.calls[0]["headers"]
    assert "X-API-Key" not in h
    assert h.get("Authorization") == "Bearer legacy-bearer"


@pytest.mark.asyncio
async def test_malformed_json_with_json_content_type_returns_raw_text() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json; charset=utf-8"},
                url=f"{BASE}/healthz",
                body_text="not-json{",
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.healthz()
    assert out == "not-json{"


@pytest.mark.asyncio
async def test_no_content_type_header_returns_body_text_not_parsed_json() -> None:
    """Нет Content-Type — не парсим как JSON, даже если тело похоже на JSON."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={},
                url=f"{BASE}/healthz",
                body_text='{"looks":"json"}',
            )
        ]
    )
    async with _make_client(fake) as client:
        out = await client.healthz()
    assert out == '{"looks":"json"}'


@pytest.mark.asyncio
async def test_post_put_delete_forward_to_request(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/a",
                body_text="{}",
            ),
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/b",
                body_text="{}",
            ),
            TransportResponse(
                status_code=204,
                headers={},
                url=f"{BASE}/c",
                body_text="",
            ),
        ]
    )
    async with _make_client(fake) as client:
        await client.post("a", json={"x": 1})
        await client.put("b", json={"y": 2})
        await client.delete("c")
    assert [c["method"] for c in fake.calls] == ["POST", "PUT", "DELETE"]


@pytest.mark.asyncio
async def test_http_error_uses_status_message_when_body_blank_only(
    no_token: None,
) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=418,
                headers={},
                url=f"{BASE}/x",
                body_text="   \n",
            )
        ]
    )
    async with _make_client(fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.get("x")
    assert str(ei.value) == "HTTP 418"
