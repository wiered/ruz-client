from __future__ import annotations

import json
from datetime import date

import pytest

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.http.transport import TransportResponse
from tests.fake_transport import FakeTransport

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
    "lecturer_id": 10,
    "discipline_id": 20,
    "auditorium_name": "101",
    "building": "ГЗ",
    "group_id": 1,
}


@pytest.mark.asyncio
async def test_get_user_day_builds_path_and_params_from_date() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/schedule/user/42/day",
                body_text=json.dumps([_LESSON]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.schedule.get_user_day(42, date(2026, 3, 26))
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/schedule/user/42/day")
    assert fake.calls[0]["params"] == {"date": "2026-03-26"}
    assert out == [_LESSON]


@pytest.mark.asyncio
async def test_get_user_day_accepts_date_string() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/schedule/user/7/day",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.schedule.get_user_day(7, "  2026-01-15  ")
    assert fake.calls[0]["params"] == {"date": "2026-01-15"}


@pytest.mark.asyncio
async def test_get_user_week_builds_path_and_params() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/schedule/user/99/week",
                body_text=json.dumps([_LESSON]),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        out = await client.schedule.get_user_week(99, date(2026, 3, 24))
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"].rstrip("/").endswith("/api/schedule/user/99/week")
    assert fake.calls[0]["params"] == {"date": "2026-03-24"}
    assert out == [_LESSON]


@pytest.mark.asyncio
async def test_get_user_day_empty_schedule_date_raises() -> None:
    fake = FakeTransport([])
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(ValueError, match="empty"):
            await client.schedule.get_user_day(1, "   ")


@pytest.mark.asyncio
async def test_get_user_day_non_list_response_raises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/schedule/user/1/day",
                body_text=json.dumps({"detail": "oops"}),
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list"):
            await client.schedule.get_user_day(1, "2026-03-26")


@pytest.mark.asyncio
async def test_get_user_week_non_list_response_raises() -> None:
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/schedule/user/1/week",
                body_text="null",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        with pytest.raises(TypeError, match="expected list"):
            await client.schedule.get_user_week(1, "2026-03-26")
