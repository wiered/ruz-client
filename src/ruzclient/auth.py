from __future__ import annotations

from typing import Mapping, Optional

from .settings import settings

API_KEY_HEADER_NAME = "X-API-Key"


def get_api_key(explicit_token: Optional[str] = None) -> Optional[str]:
    """
    Возвращает токен для заголовка `X-API-Key`.

    Приоритет:
    1) явно переданный `explicit_token`
    2) `settings.token` из переменных окружения
    """

    if explicit_token:
        return explicit_token
    # В settings.py поле называется `token`
    return getattr(settings, "token", None)


def build_auth_headers(*, token: Optional[str] = None) -> dict[str, str]:
    """Строит заголовки аутентификации (только X-API-Key при наличии токена)."""

    api_key = get_api_key(token)
    return {API_KEY_HEADER_NAME: api_key} if api_key else {}


def merge_auth_headers(
    headers: Optional[Mapping[str, str]] = None, *, token: Optional[str] = None
) -> dict[str, str]:
    """
    Мёржит переданные заголовки с аутентификацией.

    Если в `headers` уже есть `X-API-Key`, он сохраняется.
    """

    merged: dict[str, str] = dict(headers or {})
    api_headers = build_auth_headers(token=token)
    for k, v in api_headers.items():
        merged.setdefault(k, v)
    return merged