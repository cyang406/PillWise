"""A1: llm helpers. A fake OpenAI client; no network."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from pillwise import llm


class _Out(BaseModel):
    answer: str | None


class _FakeCompletions:
    def __init__(self):
        self.calls: list[dict] = []

    def parse(self, **kw):
        self.calls.append(kw)
        msg = SimpleNamespace(parsed=kw["response_format"](answer="ok"), refusal=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=" hello "))])


@pytest.fixture
def fake(monkeypatch, tmp_path):
    monkeypatch.setenv("PILLWISE_MODEL_MAIN", "gpt-test-main")
    monkeypatch.setenv("PILLWISE_MODEL_FAST", "gpt-test-fast")
    monkeypatch.setenv("PILLWISE_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("PILLWISE_OFFLINE", "0")
    comp = _FakeCompletions()
    monkeypatch.setattr(llm, "_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=comp)))
    return comp


def test_structured_uses_models_and_temperature_zero(fake):
    assert llm.structured("q", _Out).answer == "ok"
    assert fake.calls[-1]["model"] == "gpt-test-main"
    assert fake.calls[-1]["temperature"] == 0
    llm.structured("q2", _Out, fast=True)
    assert fake.calls[-1]["model"] == "gpt-test-fast"


def test_text_only_calls_are_cached(fake):
    assert llm.text("hi") == "hello"
    assert llm.text("hi") == "hello"
    assert len(fake.calls) == 1


def test_image_calls_are_never_cached(fake, tmp_path):
    llm.structured("read", _Out, image=b"\xff\xd8fake", mime_type="image/png")
    llm.structured("read", _Out, image=b"\xff\xd8fake", mime_type="image/png")
    assert len(fake.calls) == 2
    content = fake.calls[0]["messages"][1]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert not (tmp_path / "llm").exists()


def test_offline_without_cache_raises(fake, monkeypatch):
    monkeypatch.setenv("PILLWISE_OFFLINE", "1")
    with pytest.raises(llm.LLMError):
        llm.text("never seen")


def test_claude_model_name_is_rejected(fake, monkeypatch):
    monkeypatch.setenv("PILLWISE_MODEL_MAIN", "claude-sonnet-5-5")
    with pytest.raises(llm.LLMError):
        llm.structured("q", _Out)


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    llm._client.cache_clear()
    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY"):
        llm._client()
    llm._client.cache_clear()
