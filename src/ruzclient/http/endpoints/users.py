from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["UNSET", "UserCreate", "UserRead", "UserUpdate", "UsersEndpoints"]


class _UnsetType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _UnsetType()
"""Поле UserUpdate не передано в JSON (частичное обновление). None — явный JSON null."""


class UserRead(TypedDict):
    """Ответ GET /api/user/{user_id} / создания пользователя (как на сервере)."""

    id: int
    group_oid: int | None
    subgroup: int | None
    username: str
    created_at: str
    last_used_at: str


def _user_create_to_dict(c: UserCreate) -> dict[str, Any]:
    """
    POST: subgroup передаётся всегда;
    null — пользователь без назначенной подгруппы.
    """
    d = asdict(c)
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k == "subgroup":
            out[k] = v
            continue
        if v is not None:
            out[k] = v
    return out


def _user_update_to_dict(u: UserUpdate) -> dict[str, Any]:
    """
    PUT: только заданные поля;
    None сериализуется в явный null (не путать с отсутствием ключа).
    """
    out: dict[str, Any] = {}
    for f in fields(u):
        v = getattr(u, f.name)
        if v is UNSET:
            continue
        out[f.name] = v
    return out


@dataclass
class UserUpdate:
    """Тело PUT /api/user/{user_id} — частичное обновление.

    Поля по умолчанию UNSET: не попадают в JSON. Значение None отправляется как null
    (например сброс subgroup).
    """

    username: Any = UNSET
    group_oid: Any = UNSET
    subgroup: Any = UNSET
    group_guid: Any = UNSET
    group_name: Any = UNSET
    faculty_name: Any = UNSET


@dataclass
class UserCreate:
    """
    Тело POST /api/user/ (совместимо с UserCreate на сервере).

    Если группы с таким ``group_oid`` ещё нет в БД, сервер создаёт запись группы
    при непустых ``group_guid`` и ``group_name``. Поле ``faculty_name`` необязательно
    (можно не передавать — на сервере будет ``no_faculty``).

    subgroup=None сериализуется в JSON null — пользователь без подгруппы,
    пока не задана явно (0/1/2).
    """

    id: int
    username: str
    group_oid: int
    subgroup: int | None = None
    group_guid: str | None = None
    group_name: str | None = None
    faculty_name: str | None = None


class UsersEndpoints:
    """``client.users.create_user(...)``, ``client.users.get_by_id(...)`` и т.д."""

    __slots__ = ("_client",)

    def __init__(self, client: RuzClient) -> None:
        self._client = client

    async def create_user(
        self,
        payload: UserCreate,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> UserRead:
        """``POST /api/user/`` — создать пользователя."""
        body = _user_create_to_dict(payload)
        raw = await self._client.post(
            "api/user/",
            json=body,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        return raw  # type: ignore[return-value]

    async def update_user(
        self,
        user_id: int,
        payload: UserUpdate,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> UserRead:
        """``PUT /api/user/{user_id}`` — обновить пользователя."""
        body = _user_update_to_dict(payload)
        raw = await self._client.put(
            f"api/user/{user_id}",
            json=body,
            timeout_s=timeout_s,
            api_key=api_key,
        )
        return raw  # type: ignore[return-value]

    async def get_by_id(
        self,
        user_id: int,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> UserRead:
        """``GET /api/user/{user_id}`` — пользователь по id (Telegram id и т.п.)."""
        raw = await self._client.get(
            f"api/user/{user_id}",
            timeout_s=timeout_s,
            api_key=api_key,
        )
        return raw  # type: ignore[return-value]
