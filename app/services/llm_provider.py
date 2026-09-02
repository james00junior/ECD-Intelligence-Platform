"""
LLM provider abstraction for Phase 5.

Ollama is the primary local provider. OpenAI is optional and only
used when LLM_PROVIDER=openai and OPENAI_API_KEY is set.

Callers never receive database credentials through this layer.
Token/cost figures are recorded when the provider exposes them;
local Ollama inference is treated as zero cost.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from app.config.settings import get_settings


# Approximate USD per 1M tokens for optional cloud cost tracking.
_OPENAI_COST_PER_MILLION: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
}


@dataclass(frozen=True)
class LLMUsage:
    """Latency and token/cost telemetry for a single LLM call."""

    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None


@dataclass(frozen=True)
class LLMTextResult:
    """Plain-text LLM completion plus usage metadata."""

    text: str
    usage: LLMUsage


def _build_ollama_chat(
    settings,
    *,
    model: str | None = None,
) -> BaseChatModel:
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model or settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


def _build_openai_chat(
    settings,
    *,
    model: str | None = None,
) -> BaseChatModel | None:
    if not settings.openai_api_key:
        return None

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


def build_chat_model(
    llm: BaseChatModel | None = None,
    *,
    model: str | None = None,
    provider: str | None = None,
) -> BaseChatModel | None:
    """
    Return a chat model for the configured (or overridden) provider.

    Passing ``llm`` returns that instance unchanged so tests can inject
    fakes without touching the network.
    """

    if llm is not None:
        return llm

    settings = get_settings()
    selected_provider = provider or settings.llm_provider

    if selected_provider == "ollama":
        return _build_ollama_chat(settings, model=model)

    return _build_openai_chat(settings, model=model)


def _message_text(result: Any) -> str:
    if isinstance(result, str):
        return result.strip()

    if isinstance(result, BaseMessage):
        content = result.content
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "".join(parts).strip()

    content = getattr(result, "content", None)
    if isinstance(content, str):
        return content.strip()

    return str(result).strip()


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _estimate_cost_usd(
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    if provider != "openai":
        return 0.0 if provider == "ollama" else None

    rates = _OPENAI_COST_PER_MILLION.get(model)
    if rates is None or prompt_tokens is None or completion_tokens is None:
        return None

    input_rate, output_rate = rates
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def usage_from_response(
    result: Any,
    *,
    provider: str,
    model: str,
    latency_ms: float,
) -> LLMUsage:
    """Extract token counts from LangChain response metadata when present."""

    usage_meta = getattr(result, "usage_metadata", None) or {}
    response_meta = getattr(result, "response_metadata", None) or {}
    token_usage = (
        response_meta.get("token_usage")
        or response_meta.get("usage")
        or {}
    )

    prompt_tokens = _int_or_none(
        usage_meta.get("input_tokens")
        or token_usage.get("prompt_tokens")
        or response_meta.get("prompt_eval_count")
    )
    completion_tokens = _int_or_none(
        usage_meta.get("output_tokens")
        or token_usage.get("completion_tokens")
        or response_meta.get("eval_count")
    )
    total_tokens = _int_or_none(
        usage_meta.get("total_tokens")
        or token_usage.get("total_tokens")
    )

    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    return LLMUsage(
        provider=provider,
        model=model,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=_estimate_cost_usd(
            provider,
            model,
            prompt_tokens,
            completion_tokens,
        ),
    )


def complete_text(
    prompt: str,
    *,
    llm: BaseChatModel | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> LLMTextResult | None:
    """
    Run a single text completion and return usage telemetry.

    Returns None when no provider is configured.
    """

    chat = build_chat_model(llm, model=model, provider=provider)
    if chat is None:
        return None

    settings = get_settings()
    selected_provider = provider or settings.llm_provider
    selected_model = model or (
        settings.ollama_model if selected_provider == "ollama" else settings.openai_model
    )

    started = time.perf_counter()
    result = chat.invoke(prompt)
    latency_ms = (time.perf_counter() - started) * 1000

    return LLMTextResult(
        text=_message_text(result),
        usage=usage_from_response(
            result,
            provider=selected_provider,
            model=selected_model,
            latency_ms=latency_ms,
        ),
    )


__all__ = [
    "LLMTextResult",
    "LLMUsage",
    "build_chat_model",
    "complete_text",
    "usage_from_response",
]
