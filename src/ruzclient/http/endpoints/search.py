from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["RuzGroupSearchItem", "search_groups_by_name"]


class RuzGroupSearchItem(TypedDict):
    """Элемент ответа `GET /api/search/group` (как на сервере)."""

    oid: int
    name: str
    guid: str


async def search_groups_by_name(
    client: "RuzClient",
    q: str,
    *,
    timeout_s: float | None = None,
    api_key: str | None = None,
) -> list[RuzGroupSearchItem]:
    """
    Поиск групп по подстроке имени (прокси к RUZ).

    Ожидается, что ``ClientConfig.base_url`` указывает на префикс API, например
    ``http://host:8000/api`` — тогда запрос пойдёт на ``GET .../search/group?q=...``.
    """
    term = q.strip()
    if not term:
        raise ValueError("q must not be empty or whitespace-only")

    raw = await client.get(
        "search/group",
        params={"q": term},
        timeout_s=timeout_s,
        api_key=api_key,
    )
    if not isinstance(raw, list):
        raise TypeError(f"expected list from group search, got {type(raw).__name__}")
    return raw  # type: ignore[return-value]
