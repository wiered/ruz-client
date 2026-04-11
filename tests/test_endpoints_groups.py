from __future__ import annotations

import json
from uuid import UUID

import pytest

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.http.endpoints import GroupCreate, GroupUpdate
from ruzclient.http.transport import TransportResponse
from tests.fake_transport import FakeTransport

BASE = "http://127.0.0.1:2201"

_GROUP = {
    "id": 1,
    "guid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ИУ5-11",
    "faculty_name": "Факультет",
}


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
        with pytest.raises(ValueError, match="not found"):
            await client.groups.get_group(99)


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
