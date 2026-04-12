from __future__ import annotations

import json
from uuid import UUID

import pytest
from tests.fake_transport import FakeTransport

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.errors import RuzHttpError
from ruzclient.http.endpoints import GroupCreate, GroupUpdate
from ruzclient.http.endpoints.groups import GroupRead, _parse_group
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"

_GROUP: GroupRead = {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ИУ5-11",
    "faculty_name": "Факультет",
}


def test_parse_group_accepts_valid_dict() -> None:
    assert _parse_group(dict(_GROUP)) == _GROUP


def test_parse_group_rejects_non_dict() -> None:
    with pytest.raises(TypeError, match="Expected dict"):
        _parse_group([])


@pytest.mark.parametrize("missing", ["id", "guid", "name", "faculty_name"])
def test_parse_group_missing_field(missing: str) -> None:
    d = dict(_GROUP)
    del d[missing]
    with pytest.raises(KeyError, match=missing):
        _parse_group(d)


@pytest.mark.parametrize("bad_q", ["", "   ", "\t\n"])
@pytest.mark.asyncio
async def test_search_groups_rejects_empty_or_whitespace_q(bad_q: str) -> None:
    fake = FakeTransport([])
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="q must not be empty"):
            await client.groups.search_groups_by_name(bad_q)
    assert fake.calls == []


@pytest.mark.asyncio
async def test_search_groups_strips_query_and_returns_list() -> None:
    hit = {
        "oid": 1,
        "name": "ИУ5-11",
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "faculty_name": "Ф",
    }
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/search",
                body_text=json.dumps([hit]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.search_groups_by_name("  ИУ  ")
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["params"] == {"q": "ИУ"}
    assert out == [hit]


@pytest.mark.asyncio
async def test_search_groups_raises_if_response_not_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/search",
                body_text=json.dumps({"hits": []}),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list from group search"):
            await client.groups.search_groups_by_name("x")


@pytest.mark.asyncio
async def test_search_groups_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/search",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.search_groups_by_name("a", timeout_s=2.0, api_key="k")
    assert fake.calls[0]["timeout_s"] == 2.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "k"


@pytest.mark.asyncio
async def test_list_groups_empty_ok() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        assert await client.groups.list_groups() == []


@pytest.mark.asyncio
async def test_list_groups_raises_if_response_not_list() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps({"items": []}),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list from group list"):
            await client.groups.list_groups()


@pytest.mark.asyncio
async def test_list_groups_wraps_parse_error_with_index() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps([_GROUP, None]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match=r"group at index 1:"):
            await client.groups.list_groups()


@pytest.mark.asyncio
async def test_list_groups_wraps_key_error_with_index() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps([{"id": 1}]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(KeyError, match=r"group at index 0:"):
            await client.groups.list_groups()


@pytest.mark.asyncio
async def test_list_groups_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.list_groups(timeout_s=9.0, api_key="z")
    assert fake.calls[0]["timeout_s"] == 9.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "z"


@pytest.mark.asyncio
async def test_create_group_raises_on_bad_response_shape() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text="{}",
            )
        ]
    )
    payload = GroupCreate(
        id=1,
        guid="550e8400-e29b-41d4-a716-446655440000",
        name="ИУ5-11",
        faculty_name="Факультет",
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(KeyError, match="id"):
            await client.groups.create_group(payload)


@pytest.mark.asyncio
async def test_create_group_posts_json_body() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    payload = GroupCreate(
        id=1,
        guid="550e8400-e29b-41d4-a716-446655440000",
        name="ИУ5-11",
        faculty_name="Факультет",
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.create_group(payload)
    assert fake.calls[0]["method"] == "POST"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/group")
    assert fake.calls[0]["json"] == {
        "id": 1,
        "guid": "550e8400-e29b-41d4-a716-446655440000",
        "name": "ИУ5-11",
        "faculty_name": "Факультет",
    }
    assert out == _GROUP


@pytest.mark.asyncio
async def test_list_groups() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps([_GROUP]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.list_groups()
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/group")
    assert out == [_GROUP]


@pytest.mark.asyncio
async def test_get_group() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.get_group(1)
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/group/1")
    assert out == _GROUP


@pytest.mark.asyncio
async def test_get_group_by_guid_str() -> None:
    guid = "550e8400-e29b-41d4-a716-446655440000"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/guid/{guid}",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.get_group_by_guid(guid)
    assert fake.calls[0]["url"].rstrip("/").endswith(f"/api/group/guid/{guid}")
    assert out == _GROUP


@pytest.mark.asyncio
async def test_get_group_by_guid_uuid_object() -> None:
    guid = UUID("550e8400-e29b-41d4-a716-446655440000")
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/guid/{guid}",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.get_group_by_guid(guid)
    assert fake.calls[0]["url"].rstrip("/").endswith(f"/api/group/guid/{guid}")


@pytest.mark.asyncio
async def test_get_group_not_found() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=404,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/99",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="Group with id 99 not found"):
            await client.groups.get_group(99)


@pytest.mark.asyncio
async def test_get_group_non_404_http_error_reraises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=503,
                headers={},
                url=f"{BASE}/api/group/1",
                body_text="no",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.groups.get_group(1)
    assert ei.value.status_code == 503


@pytest.mark.asyncio
async def test_get_group_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.get_group(1, timeout_s=4.0, api_key="x")
    assert fake.calls[0]["timeout_s"] == 4.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "x"


@pytest.mark.asyncio
async def test_get_group_by_guid_not_found() -> None:
    guid = "550e8400-e29b-41d4-a716-446655440000"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=404,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/guid/{guid}",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match=f"Group with guid {guid!r} not found"):
            await client.groups.get_group_by_guid(guid)


@pytest.mark.asyncio
async def test_get_group_by_guid_non_404_http_error_reraises() -> None:
    guid = "550e8400-e29b-41d4-a716-446655440000"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=502,
                headers={},
                url=f"{BASE}/api/group/guid/{guid}",
                body_text="bad",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(RuzHttpError) as ei:
            await client.groups.get_group_by_guid(guid)
    assert ei.value.status_code == 502


@pytest.mark.asyncio
async def test_get_group_by_guid_passes_timeout_and_api_key(no_token: None) -> None:
    guid = "550e8400-e29b-41d4-a716-446655440000"
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/guid/{guid}",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.get_group_by_guid(guid, timeout_s=1.5, api_key="y")
    assert fake.calls[0]["timeout_s"] == 1.5
    assert fake.calls[0]["headers"].get("X-API-Key") == "y"


@pytest.mark.asyncio
async def test_update_group() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text="true",
            )
        ]
    )
    payload = GroupUpdate(name="ИУ5-12", faculty_name="Новый")
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.update_group(1, payload)
    assert fake.calls[0]["method"] == "PUT"
    assert fake.calls[0]["json"] == {"name": "ИУ5-12", "faculty_name": "Новый"}
    assert out is True


@pytest.mark.asyncio
async def test_update_group_raises_if_response_not_bool() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text=json.dumps({"ok": True}),
            )
        ]
    )
    payload = GroupUpdate(name="x", faculty_name="y")
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected bool from group update"):
            await client.groups.update_group(1, payload)


@pytest.mark.asyncio
async def test_update_group_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text="true",
            )
        ]
    )
    payload = GroupUpdate(name="a", faculty_name="b")
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.update_group(1, payload, timeout_s=6.0, api_key="u")
    assert fake.calls[0]["timeout_s"] == 6.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "u"


@pytest.mark.asyncio
async def test_delete_group() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text="true",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.delete_group(1)
    assert fake.calls[0]["method"] == "DELETE"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/group/1")
    assert out is True


@pytest.mark.asyncio
async def test_delete_group_raises_if_response_not_bool() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/1",
                body_text=json.dumps("yes"),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected bool from group delete"):
            await client.groups.delete_group(1)


@pytest.mark.asyncio
async def test_delete_group_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/7",
                body_text="false",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.delete_group(7, timeout_s=8.0, api_key="d")
    assert out is False
    assert fake.calls[0]["timeout_s"] == 8.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "d"


@pytest.mark.asyncio
async def test_create_group_passes_timeout_and_api_key(no_token: None) -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/",
                body_text=json.dumps(_GROUP),
            )
        ]
    )
    payload = GroupCreate(
        id=1,
        guid="550e8400-e29b-41d4-a716-446655440000",
        name="ИУ5-11",
        faculty_name="Факультет",
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.create_group(payload, timeout_s=5.0, api_key="c")
    assert fake.calls[0]["timeout_s"] == 5.0
    assert fake.calls[0]["headers"].get("X-API-Key") == "c"
