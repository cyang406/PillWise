import pytest


@pytest.fixture
def mock_mode(monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "1")


@pytest.fixture
def real_mode(monkeypatch):
    """Real pipeline, but no network (CLAUDE.md): RxNorm, openFDA and LLM answers come from data/cache/."""
    monkeypatch.setenv("PILLWISE_MOCK", "0")
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")
