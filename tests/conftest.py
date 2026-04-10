from __future__ import annotations

import pytest


@pytest.fixture
def no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TOKEN", raising=False)


@pytest.fixture
def env_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    key = "env-test-api-key"
    monkeypatch.setenv("TOKEN", key)
    return key
