from typing import TYPE_CHECKING, TypedDict

from ...errors import RuzHttpError

if TYPE_CHECKING:
    from ...client import RuzClient


__all__ = ["LecturersEndpoints", "Lecturer"]

_LECTURER_FIELDS = ("id", "guid", "full_name", "short_name", "rank")


class Lecturer(TypedDict):
    """Элемент ответа ``GET /api/lecturer/`` и ``GET /api/lecturer/{lecturer_id}``."""

    id: int
    guid: str
    full_name: str
    short_name: str
    rank: str


def _parse_lecturer(response: object) -> Lecturer:
    if not isinstance(response, dict):
        raise TypeError("Expected dict for lecturer response")
    for field in _LECTURER_FIELDS:
        if field not in response:
            raise KeyError(f"Missing expected field in lecturer response: '{field}'")
    return response  # type: ignore[return-value]


class LecturersEndpoints:
    __slots__ = ("_client",)

    def __init__(self, client: "RuzClient") -> None:
        self._client = client

    async def list_lecturers(
        self,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[Lecturer]:
        """Список всех преподавателей: ``GET /api/lecturer/``."""
        raw = await self._client.get(
            "api/lecturer/",
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(
                f"expected list from lecturer list, got {type(raw).__name__}"
            )
        out: list[Lecturer] = []
        for i, item in enumerate(raw):
            try:
                out.append(_parse_lecturer(item))
            except (TypeError, KeyError) as e:
                raise type(e)(f"lecturer at index {i}: {e}") from e
        return out

    async def get_lecturer(self, lecturer_id: int) -> Lecturer:
        try:
            response = await self._client.get(f"api/lecturer/{lecturer_id}")
        except RuzHttpError as e:
            if e.status_code == 404:
                raise ValueError(f"Lecturer with id {lecturer_id} not found")
            raise

        return _parse_lecturer(response)
