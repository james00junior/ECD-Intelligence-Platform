"""
Schema-aware text-to-SQL with a bounded repair loop.

The model proposes a SELECT. The existing sql_tool.validate_sql layer
and sql_guard organisation/table checks must pass before execution.
Failed generations are repaired a limited number of times, then the
caller falls back to the canned/rule planner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.config.settings import get_settings
from app.services.ecd_schema import schema_prompt
from app.services.llm_provider import LLMUsage, complete_text
from app.services.sql_guard import (
    SQLGuardError,
    sql_parameters,
    validate_generated_sql,
)


CompleteFn = Callable[[str], str]


@dataclass
class GeneratedQuery:
    """A validated SELECT plus planner telemetry."""

    sql: str
    parameters: dict[str, Any]
    source: str
    attempts: int
    repaired: bool
    latency_ms: float
    usages: list[LLMUsage] = field(default_factory=list)
    last_error: str | None = None


def _build_prompt(
    question: str,
    organisation_id: int | None,
    *,
    previous_sql: str | None = None,
    previous_error: str | None = None,
) -> str:
    schema = schema_prompt(organisation_id)
    parts = [
        schema,
        "",
        f"Question:\n{question.strip()}",
    ]
    if previous_sql and previous_error:
        parts.extend(
            [
                "",
                "The previous SQL failed validation and must be repaired.",
                f"Previous SQL:\n{previous_sql}",
                f"Validation error:\n{previous_error}",
                "Return a corrected single SELECT. Output SQL only.",
            ]
        )
    else:
        parts.append("\nWrite the SQL now.")
    return "\n".join(parts)


def _complete_with_llm(
    prompt: str,
    *,
    llm: Any = None,
    model: str | None = None,
) -> tuple[str, LLMUsage | None]:
    result = complete_text(prompt, llm=llm, model=model)
    if result is None:
        raise RuntimeError("No LLM provider is configured.")
    return result.text, result.usage


def generate_select(
    question: str,
    *,
    organisation_id: int | None,
    complete: CompleteFn | None = None,
    llm: Any = None,
    model: str | None = None,
    max_repairs: int | None = None,
) -> GeneratedQuery | None:
    """
    Generate a validated SELECT for an analytics question.

    Returns None when the model is unavailable, marks the question as
    unsupported, or cannot produce safe SQL within the repair budget.
    """

    if not isinstance(question, str) or not question.strip():
        return None

    settings = get_settings()
    repair_budget = (
        max_repairs if max_repairs is not None else settings.llm_sql_max_repairs
    )
    max_attempts = max(1, repair_budget + 1)

    usages: list[LLMUsage] = []
    total_latency_ms = 0.0
    previous_sql: str | None = None
    previous_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        prompt = _build_prompt(
            question,
            organisation_id,
            previous_sql=previous_sql,
            previous_error=previous_error,
        )

        try:
            if complete is not None:
                raw = complete(prompt)
                usage = None
            else:
                raw, usage = _complete_with_llm(prompt, llm=llm, model=model)
        except Exception:
            return None

        if usage is not None:
            usages.append(usage)
            total_latency_ms += usage.latency_ms

        try:
            sql = validate_generated_sql(
                raw,
                organisation_id=organisation_id,
            )
        except SQLGuardError as exc:
            previous_sql = (raw or "").strip()
            previous_error = str(exc)
            continue

        source = "repaired" if attempt > 1 else "generated"
        return GeneratedQuery(
            sql=sql,
            parameters=sql_parameters(sql, organisation_id),
            source=source,
            attempts=attempt,
            repaired=attempt > 1,
            latency_ms=total_latency_ms,
            usages=usages,
        )

    return None


__all__ = [
    "GeneratedQuery",
    "generate_select",
]
