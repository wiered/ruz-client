"""Инварианты JSON-тел для UserCreate / UserUpdate (не Pydantic — ручные _*_to_dict)."""

from __future__ import annotations

import pytest

from ruzclient.http.endpoints.users import (
    UserCreate,
    UserUpdate,
    _user_create_to_dict,
    _user_update_to_dict,
)

_USER_CREATE_KEYS = frozenset(
    {
        "id",
        "username",
        "group_oid",
        "subgroup",
        "group_guid",
        "group_name",
        "faculty_name",
    }
)
_USER_UPDATE_KEYS = frozenset(
    {"username", "group_oid", "subgroup", "group_guid", "group_name", "faculty_name"}
)


def test_user_create_dict_keys_never_outside_schema() -> None:
    """В теле POST только поля схемы — никаких «лишних» ключей."""
    c = UserCreate(
        id=1,
        username="u",
        group_oid=2,
        subgroup=0,
        group_guid="g",
        group_name="n",
        faculty_name="f",
    )
    d = _user_create_to_dict(c)
    assert set(d.keys()) <= _USER_CREATE_KEYS


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            UserCreate(id=1, username="x", group_oid=2),
            {"id": 1, "username": "x", "group_oid": 2, "subgroup": None},
        ),
        (
            UserCreate(id=1, username="x", group_oid=2, subgroup=1),
            {"id": 1, "username": "x", "group_oid": 2, "subgroup": 1},
        ),
        (
            UserCreate(
                id=1,
                username="x",
                group_oid=2,
                subgroup=None,
                group_guid="550e8400-e29b-41d4-a716-446655440000",
                group_name="G",
                faculty_name="F",
            ),
            {
                "id": 1,
                "username": "x",
                "group_oid": 2,
                "subgroup": None,
                "group_guid": "550e8400-e29b-41d4-a716-446655440000",
                "group_name": "G",
                "faculty_name": "F",
            },
        ),
    ],
)
def test_user_create_exclude_none_like_optional(
    payload: UserCreate, expected: dict[str, object]
) -> None:
    """
    Опциональные None (кроме subgroup) не попадают в dict — аналог exclude_none
        для опций.

    subgroup всегда в dict — даже None (явный null). Это НЕ exclude_none для subgroup.
    """
    assert _user_create_to_dict(payload) == expected


def test_user_create_omits_none_group_meta_when_partial() -> None:
    """Только group_guid задан — group_name/faculty_name с None не просачиваются."""
    d = _user_create_to_dict(
        UserCreate(
            id=1,
            username="x",
            group_oid=2,
            subgroup=1,
            group_guid="550e8400-e29b-41d4-a716-446655440000",
            group_name=None,
            faculty_name=None,
        )
    )
    assert d == {
        "id": 1,
        "username": "x",
        "group_oid": 2,
        "subgroup": 1,
        "group_guid": "550e8400-e29b-41d4-a716-446655440000",
    }


def test_user_update_empty_is_exclude_unset_all() -> None:
    """Все поля UNSET → пустой dict (аналог exclude_unset всё отфильтровал)."""
    assert _user_update_to_dict(UserUpdate()) == {}


@pytest.mark.parametrize(
    ("u", "expected"),
    [
        (UserUpdate(subgroup=None), {"subgroup": None}),
        (UserUpdate(username="a"), {"username": "a"}),
        (UserUpdate(group_oid=3, subgroup=2), {"group_oid": 3, "subgroup": 2}),
        (
            UserUpdate(
                username="u",
                group_oid=1,
                subgroup=None,
                group_guid="550e8400-e29b-41d4-a716-446655440000",
                group_name="G",
                faculty_name="F",
            ),
            {
                "username": "u",
                "group_oid": 1,
                "subgroup": None,
                "group_guid": "550e8400-e29b-41d4-a716-446655440000",
                "group_name": "G",
                "faculty_name": "F",
            },
        ),
    ],
)
def test_user_update_only_set_fields(
    u: UserUpdate, expected: dict[str, object]
) -> None:
    """UNSET не в dict; None в dict явно (не путать с отсутствием ключа)."""
    d = _user_update_to_dict(u)
    assert d == expected
    assert set(d.keys()) <= _USER_UPDATE_KEYS


def test_user_update_unset_field_not_in_dict_even_if_sibling_set() -> None:
    """Одно поле задано — остальные UNSET не появляются."""
    d = _user_update_to_dict(UserUpdate(username="only"))
    assert d == {"username": "only"}
    assert "group_oid" not in d
    assert "subgroup" not in d
