from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["ScheduleEndpoints", "UserScheduleLesson"]


class UserScheduleLesson(TypedDict):
    """Элемент ответа ``GET /api/schedule/user/{user_id}/day|week``."""

    lesson_id: int
    date: str
    begin_lesson: str
    end_lesson: str
    sub_group: int
    discipline_name: str
    kind_of_work: str
    lecturer_short_name: str
    lecturer_id: int
    discipline_id: int
    auditorium_name: str
    building: str
    group_id: int


def _format_schedule_date(d: date | str) -> str:
    if isinstance(d, date):
        return d.isoformat()
    s = d.strip()
    if not s:
        raise ValueError("date must not be empty")
    return s


class ScheduleEndpoints:
    """``client.schedule.get_user_day(...)``, ``client.schedule.get_user_week(...)``."""

    __slots__ = ("_client",)

    def __init__(self, client: RuzClient) -> None:
        self._client = client

    async def get_user_day(
        self,
        user_id: int,
        schedule_date: date | str,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Расписание пользователя за указанный день.

        Запрос: ``GET .../api/schedule/user/{user_id}/day?date=YYYY-MM-DD``.
        """
        raw = await self._client.get(
            f"api/schedule/user/{user_id}/day",
            params={"date": _format_schedule_date(schedule_date)},
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from user schedule day, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]

    async def get_user_week(
        self,
        user_id: int,
        schedule_date: date | str,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Расписание пользователя за неделю (пн–вс), якорная дата ``schedule_date``.

        Запрос: ``GET .../api/schedule/user/{user_id}/week?date=YYYY-MM-DD``.
        """
        raw = await self._client.get(
            f"api/schedule/user/{user_id}/week",
            params={"date": _format_schedule_date(schedule_date)},
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from user schedule week, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]
