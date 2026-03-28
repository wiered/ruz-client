from __future__ import annotations

import pytest

from ruzclient.settings import settings


@pytest.fixture
def no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "token", None)


@pytest.fixture
def env_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    key = "env-test-api-key"
    monkeypatch.setattr(settings, "token", key)
    return key
