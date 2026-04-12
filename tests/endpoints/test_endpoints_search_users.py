from __future__ import annotations

import json

import pytest
from tests.fake_transport import FakeTransport

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.http.endpoints import UserCreate, UserUpdate
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"


@pytest.mark.asyncio
async def test_search_groups_by_name_builds_query() -> None:
    body = json.dumps(
        [
            {
                "oid": 1,
                "name": "ИС22-1",
                "guid": "550e8400-e29b-41d4-a716-446655440000",
                "faculty_name": "Институт",
            }
        ]
    )
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/search?q=%D0%98%D0%A122",
                body_text=body,
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.groups.search_groups_by_name("  ИС22  ")
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["params"] == {"q": "ИС22"}
    assert out == [
        {
            "oid": 1,
            "name": "ИС22-1",
            "guid": "550e8400-e29b-41d4-a716-446655440000",
            "faculty_name": "Институт",
        }
    ]


@pytest.mark.asyncio
async def test_search_groups_empty_q_raises() -> None:
    fake = FakeTransport([])
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="empty"):
            await client.groups.search_groups_by_name("   ")


@pytest.mark.asyncio
async def test_create_user_posts_json_body() -> None:
    created = {
        "id": 42,
        "group_oid": 10,
        "subgroup": 0,
        "username": "u",
        "created_at": "2020-01-01T00:00:00",
        "last_used_at": "2020-01-01T00:00:00",
    }
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/",
                body_text=json.dumps(created),
            )
        ]
    )
    payload = UserCreate(
        id=42,
        username="u",
        group_oid=10,
        subgroup=0,
        group_guid="550e8400-e29b-41d4-a716-446655440000",
        group_name="G",
        faculty_name="F",
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.users.create_user(payload)
    assert fake.calls[0]["method"] == "POST"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/user")
    assert fake.calls[0]["json"] == {
        "id": 42,
        "username": "u",
        "group_oid": 10,
        "subgroup": 0,
        "group_guid": "550e8400-e29b-41d4-a716-446655440000",
        "group_name": "G",
        "faculty_name": "F",
    }
    assert out == created


@pytest.mark.asyncio
async def test_create_user_posts_null_subgroup() -> None:
    """Создание с незаданной подгруппой: в JSON уходит явный ``null``."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/",
                body_text=json.dumps(
                    {
                        "id": 1,
                        "username": "x",
                        "group_oid": 2,
                        "subgroup": None,
                        "created_at": "2020-01-01T00:00:00",
                        "last_used_at": "2020-01-01T00:00:00",
                    }
                ),
            )
        ]
    )
    payload = UserCreate(id=1, username="x", group_oid=2)
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.users.create_user(payload)
    assert fake.calls[0]["json"] == {
        "id": 1,
        "username": "x",
        "group_oid": 2,
        "subgroup": None,
    }


@pytest.mark.asyncio
async def test_update_user_put_explicit_null_subgroup() -> None:
    """PUT: явный ``null`` для subgroup отличается от отсутствия поля."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/5",
                body_text=json.dumps(
                    {
                        "id": 5,
                        "group_oid": 1,
                        "subgroup": None,
                        "username": "u",
                        "created_at": "2020-01-01T00:00:00",
                        "last_used_at": "2020-01-01T00:00:00",
                    }
                ),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.users.update_user(5, UserUpdate(subgroup=None))
    assert fake.calls[0]["method"] == "PUT"
    assert fake.calls[0]["json"] == {"subgroup": None}


@pytest.mark.asyncio
async def test_update_user_omits_unset_fields() -> None:
    """PUT: поля со значением UNSET не попадают в тело."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/5",
                body_text=json.dumps(
                    {
                        "id": 5,
                        "group_oid": 1,
                        "subgroup": 2,
                        "username": "u",
                        "created_at": "2020-01-01T00:00:00",
                        "last_used_at": "2020-01-01T00:00:00",
                    }
                ),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.users.update_user(5, UserUpdate(subgroup=2))
    assert fake.calls[0]["json"] == {"subgroup": 2}


@pytest.mark.asyncio
async def test_create_user_omits_none_optional_fields() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/",
                body_text=json.dumps(
                    {"id": 1, "username": "x", "group_oid": 2, "subgroup": 1}
                ),
            )
        ]
    )
    payload = UserCreate(id=1, username="x", group_oid=2, subgroup=1)
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.users.create_user(payload)
    assert fake.calls[0]["json"] == {
        "id": 1,
        "username": "x",
        "group_oid": 2,
        "subgroup": 1,
    }


@pytest.mark.asyncio
async def test_get_user_by_id() -> None:
    user = {
        "id": 7,
        "group_oid": 1,
        "subgroup": 0,
        "username": "tester",
        "created_at": "2020-01-01T12:00:00",
        "last_used_at": "2020-06-01T00:00:00",
    }
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/user/7",
                body_text=json.dumps(user),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.users.get_by_id(7)
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/user/7")
    assert out == user
