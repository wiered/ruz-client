from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["UserCreate", "UserRead", "UsersEndpoints"]


class UserRead(TypedDict):
    """Ответ ``GET /api/user/{user_id}`` / создания пользователя (как на сервере)."""

    id: int
    group_oid: int | None
    subgroup: int
    username: str
    created_at: str
    last_used_at: str


def _payload_as_json_dict(payload: UserCreate) -> dict[str, Any]:
    """Собирает JSON-тело; опциональные поля с ``None`` не передаются."""
    d = asdict(payload)
    return {k: v for k, v in d.items() if v is not None}


@dataclass
class UserCreate:
    """
    Тело ``POST /api/user/`` (совместимо с ``UserCreate`` на сервере).

    При создании группы в БД сервер требует ``group_guid``, ``group_name``,
    ``faculty_name`` — передайте их, если группы с таким ``group_oid`` ещё нет.
    """

    id: int
    username: str
    group_oid: int
    subgroup: int = 0
    group_guid: str | None = None
    group_name: str | None = None
    faculty_name: str | None = None


class UsersEndpoints:
    """``client.users.create_user(...)``, ``client.users.get_by_id(...)`` и т.д."""

    __slots__ = ("_client",)

    def __init__(self, client: "RuzClient") -> None:
        self._client = client

    async def create_user(
        self,
        payload: UserCreate,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> UserRead:
        """``POST /api/user/`` — создать пользователя."""
        body = _payload_as_json_dict(payload)
        raw = await self._client.post(
            "api/user/",
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
