from app.config.settings import get_settings
from app.services.llm_provider import (
    LLMUsage,
    build_chat_model,
    usage_from_response,
)


class DummyResult:
    def __init__(self):
        self.usage_metadata = {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }
        self.response_metadata = {}


def test_build_chat_model_uses_injected_llm():
    sentinel = object()
    assert build_chat_model(sentinel) is sentinel


def test_build_chat_model_openai_without_key_returns_none(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        assert build_chat_model() is None
    finally:
        get_settings.cache_clear()


def test_usage_from_response_tracks_tokens_and_local_cost():
    usage = usage_from_response(
        DummyResult(),
        provider="ollama",
        model="qwen3.5:0.8b",
        latency_ms=12.5,
    )
    assert isinstance(usage, LLMUsage)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 5
    assert usage.total_tokens == 15
    assert usage.cost_usd == 0.0
    assert usage.latency_ms == 12.5
