from __future__ import annotations


class RuzClientError(Exception):
    """Базовая ошибка клиента."""


class RuzAuthError(RuzClientError):
    """Ошибка авторизации (401/403)."""


class RuzHttpError(RuzClientError):
    """Ошибка HTTP статуса >= 400 (кроме 401/403)."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        method: str | None = None,
        url: str | None = None,
        response_text: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.method = method
        self.url = url
        self.response_text = response_text
        super().__init__(message)
