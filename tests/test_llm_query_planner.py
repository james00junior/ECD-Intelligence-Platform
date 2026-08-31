from app.config.settings import get_settings
from app.models.query_plan import AnalyticsPlan
from app.services.llm_query_planner import (
    LLMQueryPlanOutput,
    build_llm_query_plan,
)
from app.services.query_planner import build_query_plan


class FakeStructuredPlanner:
    def __init__(self, response: LLMQueryPlanOutput):
        self.response = response

    def invoke(self, inputs: dict) -> LLMQueryPlanOutput:
        assert "question" in inputs
        return self.response


def test_build_llm_query_plan_returns_supported_plan(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_query_planner._build_structured_planner",
        lambda llm=None: FakeStructuredPlanner(
            LLMQueryPlanOutput(
                intent="count_franchisees",
                reasoning="The question asks for a franchisee total.",
            )
        ),
    )

    plan = build_llm_query_plan(
        "Give me the total number of franchisees"
    )

    assert plan is not None
    assert plan.intent == "count_franchisees"
    assert plan.entity == "franchisees"
    assert plan.measure == "count"


def test_build_llm_query_plan_returns_none_for_unsupported(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_query_planner._build_structured_planner",
        lambda llm=None: FakeStructuredPlanner(
            LLMQueryPlanOutput(
                intent="unsupported",
                reasoning="Weather is outside the analytics domain.",
            )
        ),
    )

    plan = build_llm_query_plan(
        "What is the weather in Johannesburg?"
    )

    assert plan is None


def test_build_llm_query_plan_returns_none_when_planner_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.llm_query_planner._build_structured_planner",
        lambda llm=None: None,
    )

    plan = build_llm_query_plan(
        "How many franchisees are there?"
    )

    assert plan is None


def test_build_query_plan_uses_llm_mode_when_configured(monkeypatch):
    monkeypatch.setenv("QUERY_PLANNER_MODE", "llm")
    get_settings.cache_clear()

    monkeypatch.setattr(
        "app.services.llm_query_planner.build_llm_query_plan",
        lambda question, llm=None: AnalyticsPlan(
            intent="active_franchisees",
            entity="franchisees",
            measure="count",
            dimension="active",
        ),
    )

    plan = build_query_plan(
        "Show me active franchisees"
    )

    assert plan is not None
    assert plan.intent == "active_franchisees"

    get_settings.cache_clear()


def test_build_query_plan_falls_back_to_rules_when_llm_returns_none(
    monkeypatch,
):
    monkeypatch.setenv("QUERY_PLANNER_MODE", "llm")
    get_settings.cache_clear()

    monkeypatch.setattr(
        "app.services.llm_query_planner.build_llm_query_plan",
        lambda question, llm=None: None,
    )

    plan = build_query_plan(
        "How many franchisees are there?"
    )

    assert plan is not None
    assert plan.intent == "count_franchisees"

    get_settings.cache_clear()


def test_build_query_plan_uses_rules_by_default():
    plan = build_query_plan(
        "How many children are enrolled?"
    )

    assert plan is not None
    assert plan.intent == "count_children"


def test_build_chat_model_uses_ollama_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:0.8b")
    get_settings.cache_clear()

    captured: dict[str, str] = {}

    def fake_build_ollama_chat(settings):
        captured["model"] = settings.ollama_model
        captured["base_url"] = settings.ollama_base_url
        return object()

    monkeypatch.setattr(
        "app.services.llm_query_planner._build_ollama_chat",
        fake_build_ollama_chat,
    )

    from app.services.llm_query_planner import _build_chat_model

    chat = _build_chat_model()

    assert chat is not None
    assert captured["model"] == "qwen3.5:0.8b"
    assert captured["base_url"] == "http://localhost:11434"

    get_settings.cache_clear()
