from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["UserCreate", "create_user"]


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


async def create_user(
    client: "RuzClient",
    payload: UserCreate,
    *,
    timeout_s: float | None = None,
    api_key: str | None = None,
) -> Any:
    """
    Создать пользователя: ``POST /api/user/`` (ответ — как ``UserRead`` на сервере).

    Ожидается ``base_url`` с суффиксом ``/api``.
    """
    body = _payload_as_json_dict(payload)
    return await client.post(
        "user/",
        json=body,
        timeout_s=timeout_s,
        api_key=api_key,
    )
