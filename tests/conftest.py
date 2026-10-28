import pytest


@pytest.fixture
def mock_mode(monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "1")


@pytest.fixture
def real_mode(monkeypatch):
    monkeypatch.setenv("PILLWISE_MOCK", "0")
