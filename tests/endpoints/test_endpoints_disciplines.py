from __future__ import annotations

import json

import pytest
from tests.fake_transport import FakeTransport

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.errors import RuzHttpError
from ruzclient.http.endpoints.disciplines import Discipline, _parse_discipline
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"

_VALID: Discipline = {
    "id": 42,
    "name": "Математика",
    "examtype": "Экзамен",
    "has_labs": True,
}


def test_parse_discipline_accepts_valid_dict() -> None:
    out = _parse_discipline(dict(_VALID))
    assert out == _VALID


def test_parse_discipline_rejects_non_dict() -> None:
    with pytest.raises(TypeError, match="Expected dict"):
        _parse_discipline([])


@pytest.mark.parametrize("missing", ["id", "name", "examtype", "has_labs"])
def test_parse_discipline_missing_field(missing: str) -> None:
    d = dict(_VALID)
    del d[missing]
    with pytest.raises(KeyError, match=missing):
        _parse_discipline(d)


def test_parse_discipline_id_must_be_int_not_str() -> None:
    d = dict(_VALID)
    d["id"] = "42"
    with pytest.raises(TypeError, match="discipline id must be int"):
        _parse_discipline(d)


def test_parse_discipline_id_rejects_bool_even_if_subclass() -> None:
    """bool — не int для `type(rid) is not int` (True/False проходят как bool)."""
    d = dict(_VALID)
    d["id"] = True
    with pytest.raises(TypeError, match="discipline id must be int"):
        _parse_discipline(d)


def test_parse_discipline_id_rejects_float() -> None:
    d = dict(_VALID)
    d["id"] = 1.0
    with pytest.raises(TypeError, match="discipline id must be int"):
        _parse_discipline(d)


def test_parse_discipline_name_must_be_str() -> None:
    d = dict(_VALID)
    d["name"] = 99
    with pytest.raises(TypeError, match="discipline name must be str"):
        _parse_discipline(d)


def test_parse_discipline_examtype_must_be_str() -> None:
    d = dict(_VALID)
    d["examtype"] = None
    with pytest.raises(TypeError, match="discipline examtype must be str"):
        _parse_discipline(d)


def test_parse_discipline_has_labs_must_be_bool() -> None:
    d = dict(_VALID)
    d["has_labs"] = 1
    with pytest.raises(TypeError, match="discipline has_labs must be bool"):
        _parse_discipline(d)


@pytest.mark.asyncio
async def test_list_disciplines_returns_parsed_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/",
                body_text=json.dumps([_VALID, {**_VALID, "id": 2, "name": "Физика"}]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.disciplines.list_disciplines()
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/discipline")
    assert len(out) == 2
    assert out[0] == _VALID


@pytest.mark.asyncio
async def test_list_disciplines_raises_if_response_not_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/",
                body_text=json.dumps({"items": []}),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list from discipline list"):
            await client.disciplines.list_disciplines()


@pytest.mark.asyncio
async def test_list_disciplines_wraps_parse_error_with_index() -> None:
    bad = {"id": 1, "name": "x", "examtype": "y", "has_labs": "not-bool"}
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/",
                body_text=json.dumps([_VALID, bad]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match=r"discipline at index 1:"):
            await client.disciplines.list_disciplines()


@pytest.mark.asyncio
async def test_list_disciplines_wraps_key_error_with_index() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/",
                body_text=json.dumps([{"id": 1}]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(KeyError, match=r"discipline at index 0:"):
            await client.disciplines.list_disciplines()


@pytest.mark.asyncio
async def test_list_disciplines_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/",
                body_text=json.dumps([]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.disciplines.list_disciplines(timeout_s=7.5, api_key="k")
    c = fake.calls[0]
    assert c["timeout_s"] == 7.5
    assert c["headers"].get("X-API-Key") == "k"


@pytest.mark.asyncio
async def test_get_discipline_success() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/42",
                body_text=json.dumps(_VALID),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.disciplines.get_discipline(42)
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/discipline/42")
    assert out == _VALID


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_id", [0, -1])
async def test_get_discipline_rejects_non_positive_id(bad_id: int) -> None:
    fake = FakeTransport([])
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="positive integer"):
            await client.disciplines.get_discipline(bad_id)


@pytest.mark.asyncio
async def test_get_discipline_404_maps_to_value_error() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=404,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/99",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="Discipline with id 99 not found"):
            await client.disciplines.get_discipline(99)


@pytest.mark.asyncio
async def test_get_discipline_non_404_http_error_reraises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=503,
                headers={},
                url=f"{BASE}/api/discipline/1",
                body_text="unavailable",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.disciplines.get_discipline(1)
    assert ei.value.status_code == 503


@pytest.mark.asyncio
async def test_get_discipline_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/discipline/1",
                body_text=json.dumps(_VALID),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.disciplines.get_discipline(1, timeout_s=3.0, api_key="z")
    assert fake.calls[0]["timeout_s"] == 3.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "z"
