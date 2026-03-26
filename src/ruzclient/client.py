from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .auth import API_KEY_HEADER_NAME, get_api_key
from .errors import RuzAuthError, RuzClientError, RuzHttpError


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

    def __init__(self, config: ClientConfig, *, client: Optional[Any] = None) -> None:
        self._config = config

        self._own_client = client is None
        if client is not None:
            self._client = client
        else:
            try:
                import aiohttp  # type: ignore
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "aiohttp is required for RuzClient. Install it with `pip install aiohttp`."
                ) from e

            self._client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=config.timeout_s),
            )

    async def aclose(self) -> None:
        if self._own_client:
            await self._client.close()

    async def __aenter__(self) -> "RuzClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def _normalize_path(self, path: str) -> str:
        # aiohttp не имеет встроенного `base_url` в запросах, поэтому
        # делаем конкатенацию базового URL и path вручную.
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base_url = self._config.base_url.rstrip("/")
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

        # `aiohttp` задаёт таймаут через `ClientTimeout`. Для per-request override
        # создаём новый объект.
        try:
            import aiohttp  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "aiohttp is required for RuzClient. Install it with `pip install aiohttp`."
            ) from e

        timeout = aiohttp.ClientTimeout(total=timeout_value)

        try:
            async with self._client.request(
                method,
                url_or_path,
                params=params,
                json=json,
                data=data,
                headers=merged_headers or None,
                timeout=timeout,
            ) as resp:
                if resp.status in (401, 403):
                    response_text = await resp.text()
                    raise RuzAuthError(
                        f"Authorization failed with status {resp.status}: {response_text[:1000]!r}"
                    )

                if resp.status >= 400:
                    # Пытаемся отдать осмысленное сообщение (если сервер присылает JSON с detail/message).
                    response_text = await resp.text()
                    message = response_text.strip()[:1000] or f"HTTP {resp.status}"
                    raise RuzHttpError(
                        status_code=resp.status,
                        message=message,
                        method=method.upper(),
                        url=str(resp.url),
                        response_text=response_text,
                    )

                if resp.status == 204:
                    return None

                content_type = resp.headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    try:
                        return await resp.json()
                    except Exception:
                        # Если сервер заявил JSON, но вернул битый payload,
                        # отдаём текст для диагностики.
                        return await resp.text()

                return await resp.text()
        except aiohttp.ClientError as e:
            raise RuzClientError(f"Network error: {e}") from e

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

        return await self.get("/public", api_key=api_key, timeout_s=timeout_s)

    async def protected(
        self, *, api_key: Optional[str] = None, timeout_s: Optional[float] = None
    ) -> Any:
        """
        GET `/protected`.

        Требует `X-API-Key` (авторизация на стороне сервера).
        """

        return await self.get("/protected", api_key=api_key, timeout_s=timeout_s)

    async def healthz(self, *, timeout_s: Optional[float] = None) -> Any:
        """
        GET `/healthz`.

        Эндпоинт состояния сервера.
        """

        return await self.get("/healthz", timeout_s=timeout_s)

