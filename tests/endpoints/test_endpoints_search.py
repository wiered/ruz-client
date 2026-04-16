from __future__ import annotations

import json
from datetime import date

import pytest
from tests.fake_transport import FakeTransport

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"

_LESSON = {
    "lesson_id": 1,
    "date": "2026-03-26",
    "begin_lesson": "08:30:00",
    "end_lesson": "09:50:00",
    "sub_group": 0,
    "discipline_name": "Математика",
    "kind_of_work": "Лекция",
    "lecturer_short_name": "Иванов",
    "auditorium_name": "101",
    "building": "ГЗ",
    "group_id": 1,
}


@pytest.mark.asyncio
async def test_lecturer_day_path_and_params() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/search/lecturer/day",
                body_text=json.dumps([_LESSON]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.search.lecturer_day(5, date(2026, 3, 26))
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/search/lecturer/day")
    assert fake.calls[0]["params"] == {"lecturer_id": 5, "date": "2026-03-26"}
    assert out == [_LESSON]


@pytest.mark.asyncio
async def test_lecturer_week_with_optional_filters() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/search/lecturer/week",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.search.lecturer_week(2, "2026-03-24", group_id=10, sub_group=1)
    assert fake.calls[0]["params"] == {
        "lecturer_id": 2,
        "date": "2026-03-24",
        "group_id": 10,
        "sub_group": 1,
    }


@pytest.mark.asyncio
async def test_discipline_day_path_and_params() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/search/discipline/day",
                body_text=json.dumps([_LESSON]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.search.discipline_day(99, date(2026, 3, 26))
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/search/discipline/day")
    assert fake.calls[0]["params"] == {"discipline_id": 99, "date": "2026-03-26"}
    assert out == [_LESSON]


@pytest.mark.asyncio
async def test_discipline_week_path_and_params() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/search/discipline/week",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.search.discipline_week(7, date(2026, 3, 24))
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/search/discipline/week")
    assert fake.calls[0]["params"] == {"discipline_id": 7, "date": "2026-03-24"}


@pytest.mark.asyncio
async def test_lecturer_day_non_list_raises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/search/lecturer/day",
                body_text="{}",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list"):
            await client.search.lecturer_day(1, "2026-03-26")
