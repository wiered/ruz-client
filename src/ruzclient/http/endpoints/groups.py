from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, TypedDict
from uuid import UUID

from ...errors import RuzHttpError

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = [
    "GroupCreate",
    "GroupRead",
    "GroupSearchHit",
    "GroupUpdate",
    "GroupsEndpoints",
    "RuzGroupSearchItem",
]

_GROUP_FIELDS = ("id", "guid", "name", "faculty_name")


class GroupRead(TypedDict):
    """Ответ ``GET /api/group/...`` и ``POST /api/group/`` (как на сервере)."""

    id: int
    guid: str
    name: str
    faculty_name: str


class GroupSearchHit(TypedDict):
    """Элемент ответа ``GET /api/group/search`` (объединённый поиск БД + RUZ)."""

    oid: int
    name: str
    guid: str
    faculty_name: str | None


RuzGroupSearchItem = GroupSearchHit


def _guid_segment(group_guid: str | UUID) -> str:
    return str(group_guid) if isinstance(group_guid, UUID) else group_guid


def _parse_group(response: object) -> GroupRead:
    if not isinstance(response, dict):
        raise TypeError("Expected dict for group response")
    for field in _GROUP_FIELDS:
        if field not in response:
            raise KeyError(f"Missing expected field in group response: '{field}'")
    return response  # type: ignore[return-value]


@dataclass
class GroupCreate:
    """Тело ``POST /api/group/`` (совместимо с ``GroupCreate`` на сервере)."""

    id: int
    guid: str
    name: str
    faculty_name: str


@dataclass
class GroupUpdate:
    """Тело ``PUT /api/group/{group_id}``."""

    name: str
    faculty_name: str


class GroupsEndpoints:
    """Доступ к эндпоинтам групп: поиск, CRUD."""

    __slots__ = ("_client",)

    def __init__(self, client: RuzClient) -> None:
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
            raise TypeError(
                f"expected list from group search, got {type(raw).__name__}"
            )
        return raw  # type: ignore[return-value]

    async def create_group(
        self,
        payload: GroupCreate,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> GroupRead:
        """``POST /api/group/`` — создать группу."""
        raw = await self._client.post(
            "api/group/",
            json=asdict(payload),
            timeout_s=timeout_s,
            api_key=api_key,
        )
        return _parse_group(raw)

    async def list_groups(
        self,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[GroupRead]:
        """``GET /api/group/`` — список всех групп."""
        raw = await self._client.get(
            "api/group/",
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(f"expected list from group list, got {type(raw).__name__}")
        out: list[GroupRead] = []
        for i, item in enumerate(raw):
            try:
                out.append(_parse_group(item))
            except (TypeError, KeyError) as e:
                raise type(e)(f"group at index {i}: {e}") from e
        return out

    async def get_group(
        self,
        group_id: int,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> GroupRead:
        """``GET /api/group/{group_id}`` — группа по ID."""
        try:
            raw = await self._client.get(
                f"api/group/{group_id}",
                timeout_s=timeout_s,
                api_key=api_key,
            )
        except RuzHttpError as e:
            if e.status_code == 404:
                raise ValueError(f"Group with id {group_id} not found") from e
            raise
        return _parse_group(raw)

    async def get_group_by_guid(
        self,
        group_guid: str | UUID,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> GroupRead:
        """``GET /api/group/guid/{group_guid}`` — группа по GUID."""
        segment = _guid_segment(group_guid)
        try:
            raw = await self._client.get(
                f"api/group/guid/{segment}",
                timeout_s=timeout_s,
                api_key=api_key,
            )
        except RuzHttpError as e:
            if e.status_code == 404:
                raise ValueError(f"Group with guid {segment!r} not found") from e
            raise
        return _parse_group(raw)

    async def update_group(
        self,
        group_id: int,
        payload: GroupUpdate,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> bool:
        """``PUT /api/group/{group_id}`` — обновить название и факультет."""
        raw = await self._client.put(
            f"api/group/{group_id}",
            json=asdict(payload),
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, bool):
            raise TypeError(
                f"expected bool from group update, got {type(raw).__name__}"
            )
        return raw

    async def delete_group(
        self,
        group_id: int,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> bool:
        """``DELETE /api/group/{group_id}`` — удалить группу."""
        raw = await self._client.delete(
            f"api/group/{group_id}",
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, bool):
            raise TypeError(
                f"expected bool from group delete, got {type(raw).__name__}"
            )
        return raw
