"""Поиск групп: Unicode, пробелы, % и спецсимволы в `q` (параметры GET)."""

from __future__ import annotations

import pytest
from tests.fake_transport import FakeTransport
from yarl import URL

from ruzclient.client import ClientConfig, RuzClient
from ruzclient.http.transport import TransportResponse

BASE = "http://127.0.0.1:2201"
GROUP_SEARCH_PATH = f"{BASE}/api/group/search"


@pytest.mark.parametrize(
    ("raw_q", "expected_q"),
    [
        ("  ИС22-1  ", "ИС22-1"),
        ("ИУ 5-11", "ИУ 5-11"),
        ("a b c", "a b c"),
        ("%20", "%20"),
        ("100% успех", "100% успех"),
        ("foo&bar=1", "foo&bar=1"),
        ("x?y", "x?y"),
        ("x#frag", "x#frag"),
        ("тест+плюс", "тест+плюс"),
        ("🎓 группа", "🎓 группа"),
        ("ИУ 5-11 (МСК)", "ИУ 5-11 (МСК)"),
    ],
)
@pytest.mark.asyncio
async def test_search_groups_passes_unicode_and_specials_as_param(
    raw_q: str, expected_q: str
) -> None:
    """Клиент передаёт в транспорт ту же Unicode-строку, без потери символов."""
    fake = FakeTransport(
        [
            TransportResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                url=f"{BASE}/api/group/search",
                body_text="[]",
            )
        ]
    )
    async with RuzClient(ClientConfig(base_url=BASE), transport=fake) as client:
        await client.groups.search_groups_by_name(raw_q)
    assert fake.calls[0]["params"] == {"q": expected_q}


@pytest.mark.parametrize(
    "q",
    [
        "ИС22",
        "ИУ 5-11",
        "%20",
        "100% успех",
        "foo&bar=1",
        "тест+плюс",
        "🎓 группа",
    ],
)
def test_yarl_query_encoding_round_trips(q: str) -> None:
    """aiohttp/yarl: после `with_query` значение `q` совпадает с исходной строкой."""
    u = URL(GROUP_SEARCH_PATH).with_query({"q": q})
    assert u.query["q"] == q


@pytest.mark.parametrize(
    "q_with_space",
    ["ИУ 5-11", "a b", "🎓 x"],
)
def test_yarl_query_string_has_no_literal_spaces(q_with_space: str) -> None:
    """В строке query нет «сырых» пробелов (пробел → + или %20)."""
    u = URL(GROUP_SEARCH_PATH).with_query({"q": q_with_space})
    query_fragment = str(u).split("?", 1)[1].split("#", 1)[0]
    assert " " not in query_fragment
