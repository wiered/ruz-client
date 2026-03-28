from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .auth import API_KEY_HEADER_NAME, get_api_key
from .errors import RuzAuthError, RuzHttpError
from .http import AiohttpTransport
from .http.transport import AsyncHttpTransport, TransportResponse


def _normalize_base_url(base_url: str, *, default_scheme: str = "http", default_port: int = 2201) -> str:
    """
    Приводит `base_url` к виду `http[s]://host[:port][/path]`.

    Нужна устойчивость к BASE_URL из env, который иногда задан как `127.0.0.1`.
    """

    cleaned = base_url.strip().rstrip("/")
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned

    # Отделяем "хост/порт" от возможного пути (/api).
    if "/" in cleaned:
        host_part, rest = cleaned.split("/", 1)
        rest = "/" + rest if rest else ""
    else:
        host_part, rest = cleaned, ""

    # Если порт не указан, добавляем default_port.
    if ":" not in host_part:
        host_part = f"{host_part}:{default_port}"

    return f"{default_scheme}://{host_part}{rest}"


def _content_type_lower(headers: Mapping[str, str]) -> str:
    for k, v in headers.items():
        if k.lower() == "content-type":
            return v.lower()
    return ""


@dataclass(frozen=True)
class ClientConfig:
    base_url: str
    timeout_s: float = 30.0
    # API Key для `X-API-Key` (требуется ruz-server по документации).
    api_key: Optional[str] = None
    # Оставлено для обратной совместимости: если `api_key` не задан,
    # используем `bearer_token` как источник для `X-API-Key`.
    bearer_token: Optional[str] = None
    default_headers: Optional[Mapping[str, str]] = None


class RuzClient:
    """
    Асинхронный клиент для `/ruz-server`.

    Цель этого модуля - дать устойчивую базу:
    - единый wrapper над HTTP-запросами
    - базовая обработка ошибок
    - парсинг JSON/текста
    """

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: Optional[AsyncHttpTransport] = None,
        client: Optional[Any] = None,
    ) -> None:
        self._config = ClientConfig(
            base_url=_normalize_base_url(config.base_url),
            timeout_s=config.timeout_s,
            api_key=config.api_key,
            bearer_token=config.bearer_token,
            default_headers=config.default_headers,
        )

        if transport is not None and client is not None:
            raise ValueError("Pass only one of `transport` or `client`, not both.")

        if transport is not None:
            self._transport = transport
            self._own_transport = False
        elif client is not None:
            self._transport = AiohttpTransport(session=client)
            self._own_transport = False
        else:
            self._transport = AiohttpTransport(timeout_s=config.timeout_s)
            self._own_transport = True

    async def aclose(self) -> None:
        if self._own_transport:
            await self._transport.aclose()

    async def __aenter__(self) -> "RuzClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def _normalize_path(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base_url = self._config.base_url.rstrip("/")
        path_norm = path.lstrip("/")
        if not path_norm:
            return base_url
        return f"{base_url}/{path_norm}"

    def _normalize_root_path(self, path: str) -> str:
        """
        Нормализует путь относительно "корня" сервера.

        В ваших доках встречается `BASE_URL` вида `http://host:8000/api`,
        но эндпоинты `/public`, `/protected`, `/healthz` объявлены в `app.py`
        без префикса `/api`. Поэтому, если base_url заканчивается на `/api`,
        отрежем его для этих методов.
        """

        if path.startswith("http://") or path.startswith("https://"):
            return path

        base_url = self._config.base_url.rstrip("/")
        if base_url.endswith("/api"):
            base_url = base_url[: -len("/api")]

        path_norm = path.lstrip("/")
        if not path_norm:
            return base_url
        return f"{base_url}/{path_norm}"

    def _build_headers(
        self,
        headers: Optional[Mapping[str, str]],
        *,
        api_key: Optional[str] = None,
    ) -> dict[str, str]:
        merged: dict[str, str] = {}
        if self._config.default_headers:
            merged.update(dict(self._config.default_headers))
        if headers:
            merged.update(dict(headers))

        # Всегда передаём `X-API-Key` с каждым запросом (если токен доступен).
        effective_api_key = api_key
        if effective_api_key is None:
            effective_api_key = (
                self._config.api_key
                if self._config.api_key is not None
                else (self._config.bearer_token if self._config.bearer_token is not None else None)
            )
        if effective_api_key is None:
            effective_api_key = get_api_key()

        if effective_api_key:
            merged.setdefault(API_KEY_HEADER_NAME, effective_api_key)
        elif self._config.bearer_token and "Authorization" not in merged:
            # Фоллбэк для старой схемы (если вдруг используются старые эндпоинты).
            merged.setdefault("Authorization", f"Bearer {self._config.bearer_token}")

        return merged

    def _apply_response_policy(self, method: str, resp: TransportResponse) -> Any:
        if resp.status_code in (401, 403):
            snippet = resp.body_text[:1000]
            raise RuzAuthError(
                f"Authorization failed with status {resp.status_code}: {snippet!r}"
            )

        if resp.status_code >= 400:
            message = resp.body_text.strip()[:1000] or f"HTTP {resp.status_code}"
            raise RuzHttpError(
                status_code=resp.status_code,
                message=message,
                method=method.upper(),
                url=resp.url,
                response_text=resp.body_text,
            )

        if resp.status_code == 204:
            return None

        content_type = _content_type_lower(resp.headers)
        if "application/json" in content_type:
            try:
                return json.loads(resp.body_text)
            except Exception:
                # Если сервер заявил JSON, но вернул битый payload,
                # отдаём текст для диагностики.
                return resp.body_text

        return resp.body_text

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        """
        Унифицированный запрос.

        Возвращает:
        - parsed JSON, если ответ похож на JSON
        - текст, если не JSON
        - None для 204 No Content
        """
        url_or_path = self._normalize_path(path)
        merged_headers = self._build_headers(headers, api_key=api_key)

        timeout_value = timeout_s if timeout_s is not None else self._config.timeout_s

        resp = await self._transport.send(
            method,
            url_or_path,
            params=params,
            json=json,
            data=data,
            headers=merged_headers or None,
            timeout_s=timeout_value,
        )
        return self._apply_response_policy(method, resp)

    async def get(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        return await self.request(
            "GET",
            path,
            params=params,
            headers=headers,
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def post(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        return await self.request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def put(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        return await self.request(
            "PUT",
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def delete(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        api_key: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        return await self.request(
            "DELETE",
            path,
            params=params,
            headers=headers,
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def public(self, *, api_key: Optional[str] = None, timeout_s: Optional[float] = None) -> Any:
        """
        GET `/public`.

        Эндпоинт публичный, но заголовок `X-API-Key` не мешает (если токен доступен).
        """

        return await self.request(
            "GET",
            self._normalize_root_path("/public"),
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def protected(
        self, *, api_key: Optional[str] = None, timeout_s: Optional[float] = None
    ) -> Any:
        """
        GET `/protected`.

        Требует `X-API-Key` (авторизация на стороне сервера).
        """

        return await self.request(
            "GET",
            self._normalize_root_path("/protected"),
            api_key=api_key,
            timeout_s=timeout_s,
        )

    async def healthz(self, *, timeout_s: Optional[float] = None) -> Any:
        """
        GET `/healthz`.

        Эндпоинт состояния сервера.
        """

        return await self.request(
            "GET",
            self._normalize_root_path("/healthz"),
            timeout_s=timeout_s,
        )
