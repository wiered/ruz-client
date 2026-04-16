from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import RuzClient

from .schedule import UserScheduleLesson, _format_schedule_date

__all__ = ["SearchEndpoints", "search_group_filters"]


def _optional_filters(
    *,
    group_id: int | None,
    sub_group: int | None,
) -> dict[str, int]:
    out: dict[str, int] = {}
    if group_id is not None:
        out["group_id"] = group_id
    if sub_group is not None:
        out["sub_group"] = sub_group
    return out


def search_group_filters(
    *,
    group_id: int | None = None,
    sub_group: int | None = None,
) -> dict[str, int]:
    """Дополнительные query-параметры group_id / sub_group для GET .../api/search/..."""
    return _optional_filters(group_id=group_id, sub_group=sub_group)


class SearchEndpoints:
    """``client.search.lecturer_day(...)``, ``discipline_week(...)``, …"""

    __slots__ = ("_client",)

    def __init__(self, client: RuzClient) -> None:
        self._client = client

    async def lecturer_day(
        self,
        lecturer_id: int,
        schedule_date: date | str,
        *,
        group_id: int | None = None,
        sub_group: int | None = None,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Занятия преподавателя за день.

        Запрос: ``GET .../api/search/lecturer/day``.
        """
        params: dict[str, str | int] = {
            "lecturer_id": lecturer_id,
            "date": _format_schedule_date(schedule_date),
            **_optional_filters(group_id=group_id, sub_group=sub_group),
        }
        raw = await self._client.get(
            "api/search/lecturer/day",
            params=params,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from lecturer day search, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]

    async def lecturer_week(
        self,
        lecturer_id: int,
        schedule_date: date | str,
        *,
        group_id: int | None = None,
        sub_group: int | None = None,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Занятия преподавателя за неделю (пн–вс), якорная дата ``schedule_date``.

        Запрос: ``GET .../api/search/lecturer/week``.
        """
        params: dict[str, str | int] = {
            "lecturer_id": lecturer_id,
            "date": _format_schedule_date(schedule_date),
            **_optional_filters(group_id=group_id, sub_group=sub_group),
        }
        raw = await self._client.get(
            "api/search/lecturer/week",
            params=params,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from lecturer week search, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]

    async def discipline_day(
        self,
        discipline_id: int,
        schedule_date: date | str,
        *,
        group_id: int | None = None,
        sub_group: int | None = None,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Занятия по дисциплине за день.

        Запрос: ``GET .../api/search/discipline/day``.
        """
        params: dict[str, str | int] = {
            "discipline_id": discipline_id,
            "date": _format_schedule_date(schedule_date),
            **_optional_filters(group_id=group_id, sub_group=sub_group),
        }
        raw = await self._client.get(
            "api/search/discipline/day",
            params=params,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from discipline day search, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]

    async def discipline_week(
        self,
        discipline_id: int,
        schedule_date: date | str,
        *,
        group_id: int | None = None,
        sub_group: int | None = None,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[UserScheduleLesson]:
        """
        Занятия по дисциплине за неделю (пн–вс), якорная дата ``schedule_date``.

        Запрос: ``GET .../api/search/discipline/week``.
        """
        params: dict[str, str | int] = {
            "discipline_id": discipline_id,
            "date": _format_schedule_date(schedule_date),
            **_optional_filters(group_id=group_id, sub_group=sub_group),
        }
        raw = await self._client.get(
            "api/search/discipline/week",
            params=params,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from discipline week search, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]
