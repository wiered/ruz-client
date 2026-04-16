from __future__ import annotations

import json

import pytest
from tests.fake_transport import FakeTransport

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.errors import RuzHttpError
from ruzclient.http.endpoints.lecturers import Lecturer, _parse_lecturer
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"

_VALID: Lecturer = {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "Иванов Иван Иванович",
    "short_name": "Иванов И.И.",
    "rank": "доцент",
}


def test_parse_lecturer_accepts_valid_dict() -> None:
    out = _parse_lecturer(dict(_VALID))
    assert out == _VALID


def test_parse_lecturer_accepts_extra_keys() -> None:
    """API может отдавать поля сверх схемы — парсер их не отбрасывает."""
    d = {**_VALID, "department": "ФМиИТ"}
    out = _parse_lecturer(d)
    assert out["department"] == "ФМиИТ"
    assert out["id"] == _VALID["id"]


def test_parse_lecturer_rejects_non_dict() -> None:
    with pytest.raises(TypeError, match="Expected dict"):
        _parse_lecturer([])


@pytest.mark.parametrize("missing", ["id", "guid", "full_name", "short_name", "rank"])
def test_parse_lecturer_missing_field(missing: str) -> None:
    d = dict(_VALID)
    del d[missing]
    with pytest.raises(KeyError, match=missing):
        _parse_lecturer(d)


@pytest.mark.asyncio
async def test_list_lecturers_returns_parsed_list() -> None:
    second = {**_VALID, "id": 2, "short_name": "Петров П.П."}
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps([_VALID, second]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.lecturers.list_lecturers()
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/lecturer")
    assert len(out) == 2
    assert out[0] == _VALID
    assert out[1]["id"] == 2


@pytest.mark.asyncio
async def test_list_lecturers_empty_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.lecturers.list_lecturers()
    assert out == []


@pytest.mark.asyncio
async def test_list_lecturers_raises_if_response_not_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps({"lecturers": []}),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list from lecturer list"):
            await client.lecturers.list_lecturers()


@pytest.mark.asyncio
async def test_list_lecturers_wraps_type_error_with_index() -> None:
    bad = "not-a-dict"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps([_VALID, bad]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match=r"lecturer at index 1:"):
            await client.lecturers.list_lecturers()


@pytest.mark.asyncio
async def test_list_lecturers_wraps_key_error_with_index() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps([{"id": 1}]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(KeyError, match=r"lecturer at index 0:"):
            await client.lecturers.list_lecturers()


@pytest.mark.asyncio
async def test_list_lecturers_wraps_error_at_index_zero() -> None:
    """Первый элемент списка может быть битым — индекс в сообщении 0."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps([None]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match=r"lecturer at index 0:"):
            await client.lecturers.list_lecturers()


@pytest.mark.asyncio
async def test_list_lecturers_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/",
                body_text=json.dumps([]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.lecturers.list_lecturers(timeout_s=7.5, api_key="k")
    c = fake.calls[0]
    assert c["timeout_s"] == 7.5
    assert c["headers"].get("X-API-Key") == "k"


@pytest.mark.asyncio
async def test_get_lecturer_success() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/1",
                body_text=json.dumps(_VALID),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.lecturers.get_lecturer(1)
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/lecturer/1")
    assert out == _VALID


@pytest.mark.asyncio
async def test_get_lecturer_404_maps_to_value_error() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=404,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/404",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="Lecturer with id 404 not found"):
            await client.lecturers.get_lecturer(404)


@pytest.mark.asyncio
async def test_get_lecturer_non_404_http_error_reraises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=503,
                headers={},
                url=f"{BASE}/api/lecturer/1",
                body_text="unavailable",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.lecturers.get_lecturer(1)
    assert ei.value.status_code == 503


@pytest.mark.asyncio
async def test_get_lecturer_invalid_json_shape_raises_from_parse() -> None:
    """Успешный HTTP 200, но объект без полей — ошибка парсера, не ValueError."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/1",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(KeyError, match="id"):
            await client.lecturers.get_lecturer(1)


@pytest.mark.asyncio
async def test_get_lecturer_non_dict_json_raises_type_error() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/lecturer/1",
                body_text=json.dumps([_VALID]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="Expected dict"):
            await client.lecturers.get_lecturer(1)
