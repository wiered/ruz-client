from __future__ import annotations

import pytest

from ruzclient.auth import (
    API_KEY_HEADER_NAME,
    build_auth_headers,
    get_api_key,
    merge_auth_headers,
)


def test_get_api_key_returns_explicit_token() -> None:
    assert get_api_key("cli-token") == "cli-token"


def test_get_api_key_falls_back_to_env(
    no_token: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TOKEN", "from-env")
    assert get_api_key(None) == "from-env"


def test_get_api_key_explicit_empty_string_falls_back_to_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Пустая строка не считается явным токеном — берётся переменная окружения."""
    monkeypatch.setenv("TOKEN", "env-wins")
    assert get_api_key("") == "env-wins"


def test_get_api_key_missing_returns_none(no_token: None) -> None:
    assert get_api_key(None) is None


def test_get_api_key_whitespace_only_string_is_truthy() -> None:
    """Строка из пробелов считается явным токеном (truthy) и возвращается как есть."""
    assert get_api_key("   ") == "   "


def test_build_auth_headers_with_explicit_token() -> None:
    assert build_auth_headers(token="t") == {API_KEY_HEADER_NAME: "t"}


def test_build_auth_headers_from_env(env_api_key: str) -> None:
    assert build_auth_headers(token=None) == {API_KEY_HEADER_NAME: env_api_key}


def test_build_auth_headers_empty_when_no_token(no_token: None) -> None:
    assert build_auth_headers(token=None) == {}


def test_merge_auth_headers_none_headers_uses_auth_only(env_api_key: str) -> None:
    assert merge_auth_headers(None, token=None) == {API_KEY_HEADER_NAME: env_api_key}


def test_merge_auth_headers_preserves_existing_api_key() -> None:
    existing = {
        API_KEY_HEADER_NAME: "already-set",
        "Accept": "application/json",
    }
    merged = merge_auth_headers(
        existing,
        token="would-override-if-not-setdefault",
    )
    assert merged[API_KEY_HEADER_NAME] == "already-set"
    assert merged["Accept"] == "application/json"


def test_merge_auth_headers_adds_key_when_absent() -> None:
    base = {"Accept": "application/json"}
    merged = merge_auth_headers(base, token="new-key")
    assert merged[API_KEY_HEADER_NAME] == "new-key"
    assert merged["Accept"] == "application/json"


def test_merge_auth_headers_empty_base_dict_with_token() -> None:
    assert merge_auth_headers({}, token="x") == {API_KEY_HEADER_NAME: "x"}


def test_merge_auth_headers_no_token_no_extra_keys(no_token: None) -> None:
    assert merge_auth_headers({"User-Agent": "t"}, token=None) == {"User-Agent": "t"}


def test_merge_auth_headers_lowercase_api_key_not_deduped() -> None:
    """Ключи чувствительны к регистру: x-api-key и X-API-Key — разные ключи dict."""
    merged = merge_auth_headers({"x-api-key": "lower"}, token="upper")
    assert merged["x-api-key"] == "lower"
    assert merged[API_KEY_HEADER_NAME] == "upper"
