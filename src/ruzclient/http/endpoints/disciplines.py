from typing import TYPE_CHECKING, TypedDict

from ...errors import RuzHttpError

if TYPE_CHECKING:
    from ...client import RuzClient

__all__ = ["DisciplinesEndpoints", "Discipline"]

_DISCIPLINE_FIELDS = ("id", "name", "examtype", "has_labs")


def _parse_discipline(response: object) -> "Discipline":
    """
    Parse a discipline object from the API response.

    Raises:
        TypeError: If response is not a dict or field types do not match the schema.
        KeyError: If required fields are missing.
    """
    if not isinstance(response, dict):
        raise TypeError("Expected dict for discipline response")
    for field in _DISCIPLINE_FIELDS:
        if field not in response:
            raise KeyError(f"Missing expected field in discipline response: '{field}'")

    rid = response["id"]
    if type(rid) is not int:
        raise TypeError(f"discipline id must be int, got {type(rid).__name__}")
    name = response["name"]
    if not isinstance(name, str):
        raise TypeError(f"discipline name must be str, got {type(name).__name__}")
    examtype = response["examtype"]
    if not isinstance(examtype, str):
        raise TypeError(f"discipline examtype must be str, got {type(examtype).__name__}")
    has_labs = response["has_labs"]
    if not isinstance(has_labs, bool):
        raise TypeError(f"discipline has_labs must be bool, got {type(has_labs).__name__}")

    return response  # type: ignore[return-value]

class Discipline(TypedDict):
    """Item returned by ``GET /api/discipline/`` and ``GET /api/discipline/{discipline_id}``."""
    id: int
    name: str
    examtype: str
    has_labs: bool

class DisciplinesEndpoints:
    __slots__ = ("_client",)

    def __init__(self, client: "RuzClient") -> None:
        self._client = client

    async def list_disciplines(
        self,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> list[Discipline]:
        """
        GET /api/discipline/

        Returns a list of all disciplines.

        Raises:
            TypeError: If the response is not a JSON array or an item has the wrong shape.
            KeyError: If a list item is missing a required field.
            RuzHttpError: On HTTP error from the server.
        """
        raw = await self._client.get(
            "api/discipline/",
            timeout_s=timeout_s,
            api_key=api_key,
        )
        if not isinstance(raw, list):
            raise TypeError(f"expected list from discipline list, got {type(raw).__name__}")
        out: list[Discipline] = []
        for i, item in enumerate(raw):
            try:
                out.append(_parse_discipline(item))
            except (TypeError, KeyError) as e:
                raise type(e)(f"discipline at index {i}: {e}") from e
        return out

    async def get_discipline(
        self,
        discipline_id: int,
        *,
        timeout_s: float | None = None,
        api_key: str | None = None,
    ) -> Discipline:
        """
        GET /api/discipline/{discipline_id}

        Returns a discipline by its ID.

        Args:
            discipline_id: ID of the discipline.

        Returns:
            Discipline: The found discipline.

        Raises:
            ValueError: If ``discipline_id`` is not a positive integer, or the discipline does not exist (404).
            TypeError: If the response body is not a discipline-shaped object.
            KeyError: If a required field is missing from the response.
            RuzHttpError: On other HTTP errors.
        """
        if discipline_id < 1:
            raise ValueError("discipline_id must be a positive integer")

        try:
            resp = await self._client.get(
                f"api/discipline/{discipline_id}",
                timeout_s=timeout_s,
                api_key=api_key,
            )
        except RuzHttpError as e:
            if e.status_code == 404:
                raise ValueError(f"Discipline with id {discipline_id} not found") from e
            raise

        return _parse_discipline(resp)