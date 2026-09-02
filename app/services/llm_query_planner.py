"""
LLM-backed query planner for Phase 3.

Uses structured LLM output to classify analytics questions into supported
intents, then maps those intents to canonical AnalyticsPlan objects.

Default provider is Ollama for local inference. OpenAI remains available
as an optional provider.

When the LLM is unavailable or returns an unsupported intent, callers
should fall back to the rule-based planner.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.models.query_plan import AnalyticsPlan
from app.services.llm_provider import build_chat_model
from app.services.query_planner import VALID_INTENTS, plan_from_intent


SUPPORTED_INTENTS: tuple[str, ...] = tuple(sorted(VALID_INTENTS))


class LLMQueryPlanOutput(BaseModel):
    """Structured LLM response for analytics query planning."""

    intent: Literal[
        "count_franchisees",
        "active_franchisees",
        "count_children",
        "franchisees_by_status",
        "franchisees_by_province",
        "franchisees_by_main_place",
        "children_by_province",
        "population_by_province",
        "unsupported",
    ] = Field(
        description=(
            "The analytics intent for the question, or 'unsupported' "
            "when the question cannot be answered with the available data."
        ),
    )
    reasoning: str | None = Field(
        default=None,
        description="Brief explanation of why this intent was selected.",
    )


PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an analytics query planner for an ECD intelligence platform.

Your job is to classify natural-language questions into exactly one supported
analytics intent, or mark the question as unsupported.

Supported intents:
- count_franchisees: total number of franchisees
- active_franchisees: number of active franchisees
- count_children: total enrolled children
- franchisees_by_status: franchisee counts grouped by status
- franchisees_by_province: franchisee counts grouped by province
- franchisees_by_main_place: franchisee counts grouped by main place
- children_by_province: enrolled children grouped by residential province
- population_by_province: population totals grouped by province

Use unsupported for questions outside this analytics domain.""",
        ),
        (
            "human",
            "Classify this analytics question:\n\n{question}",
        ),
    ]
)


def _build_ollama_chat(settings) -> BaseChatModel:
    return build_chat_model(provider="ollama", model=settings.ollama_model)


def _build_openai_chat(settings) -> BaseChatModel | None:
    return build_chat_model(provider="openai", model=settings.openai_model)


def _build_chat_model(
    llm: BaseChatModel | None = None,
) -> BaseChatModel | None:
    if llm is not None:
        return llm

    settings = get_settings()

    if settings.llm_provider == "ollama":
        return _build_ollama_chat(settings)

    return _build_openai_chat(settings)


def _build_structured_planner(
    llm: BaseChatModel | None = None,
):
    chat = _build_chat_model(llm)

    if chat is None:
        return None

    return PLANNER_PROMPT | chat.with_structured_output(
        LLMQueryPlanOutput
    )


def build_llm_query_plan(
    question: str,
    *,
    llm: BaseChatModel | None = None,
) -> AnalyticsPlan | None:
    """
    Create an AnalyticsPlan using LLM structured output.

    Returns None when:
    - no LLM provider is configured
    - the LLM call fails
    - the LLM marks the question as unsupported
    """

    planner = _build_structured_planner(llm)

    if planner is None:
        return None

    try:
        result = planner.invoke({"question": question})
    except Exception:
        return None

    if not isinstance(result, LLMQueryPlanOutput):
        return None

    if result.intent == "unsupported":
        return None

    if result.intent not in VALID_INTENTS:
        return None

    return plan_from_intent(result.intent)


__all__ = [
    "LLMQueryPlanOutput",
    "build_llm_query_plan",
]
