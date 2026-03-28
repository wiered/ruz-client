from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["GroupSearchHit", "GroupsEndpoints", "RuzGroupSearchItem"]


class GroupSearchHit(TypedDict):
    """Элемент ответа ``GET /api/group/search`` (объединённый поиск БД + RUZ)."""

    oid: int
    name: str
    guid: str
    faculty_name: str | None


RuzGroupSearchItem = GroupSearchHit


class GroupsEndpoints:
    """Доступ к эндпоинтам групп: ``client.groups.search_groups_by_name(...)``."""

    __slots__ = ("_client",)

    def __init__(self, client: "RuzClient") -> None:
        self._client = client

    async def search_groups_by_name(
        self,
        q: str,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[GroupSearchHit]:
        """
        Поиск групп по имени в локальной БД и на ruz.mstuca.ru.

        Базовый URL без суффикса ``/api`` (например ``http://host:8000``);
        запрос: ``GET .../api/group/search?q=...``.
        """
        term = q.strip()
        if not term:
            raise ValueError("q must not be empty or whitespace-only")

        raw = await self._client.get(
            "api/group/search",
            params={"q": term},
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(f"expected list from group search, got {type(raw).__name__}")
        return raw  # type: ignore[return-value]
