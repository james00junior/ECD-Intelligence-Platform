"""
Turn SQL result rows into a natural-language analytics answer.

Strategy:
- Canned intents keep the existing deterministic templates.
- Generated SQL uses a solid deterministic renderer so answers still
  work when the model is down.
- When QUERY_PLANNER_MODE=llm, an optional LLM phrasing pass is tried
  first; any failure falls back to the deterministic renderer.
"""

from __future__ import annotations

from typing import Any

from app.agents.response_generator import generate_response
from app.config.settings import get_settings
from app.services.query_planner import VALID_INTENTS


def _format_cell(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    return str(value)


def render_rows(
    question: str,
    results: list[dict[str, Any]],
    *,
    limit: int = 12,
) -> str:
    """Deterministic renderer for arbitrary SELECT results."""

    if not results:
        return "No results were found."

    if len(results) == 1 and len(results[0]) == 1:
        key, value = next(iter(results[0].items()))
        label = key.replace("_", " ")
        return f"{label.capitalize()}: {_format_cell(value)}."

    if len(results) == 1:
        parts = [
            f"{key.replace('_', ' ')}: {_format_cell(value)}"
            for key, value in results[0].items()
        ]
        return "Result — " + "; ".join(parts) + "."

    headers = list(results[0].keys())
    if len(headers) == 2:
        group_key, value_key = headers
        lines = [f"Results for: {question.strip()}"]
        for row in results[:limit]:
            lines.append(
                f"- {_format_cell(row.get(group_key))}: "
                f"{_format_cell(row.get(value_key))}"
            )
        if len(results) > limit:
            lines.append(f"- … and {len(results) - limit} more")
        return "\n".join(lines)

    lines = [f"Results for: {question.strip()}"]
    for row in results[:limit]:
        cells = ", ".join(
            f"{key.replace('_', ' ')}={_format_cell(value)}"
            for key, value in row.items()
        )
        lines.append(f"- {cells}")
    if len(results) > limit:
        lines.append(f"- … and {len(results) - limit} more")
    return "\n".join(lines)


def _llm_interpret(
    question: str,
    results: list[dict[str, Any]],
) -> str | None:
    from app.services.llm_provider import complete_text

    sample = results[:12]
    prompt = (
        "You convert SQL analytics results into a short, factual answer "
        "for an ECD operations user. Use only the provided rows. Do not "
        "invent numbers. If the rows are empty, say no results were found.\n\n"
        f"Question: {question.strip()}\n"
        f"Rows: {sample!r}\n\n"
        "Answer in 1-4 sentences or a compact bullet list."
    )
    try:
        result = complete_text(prompt)
    except Exception:
        return None
    if result is None or not result.text:
        return None
    return result.text


def interpret_results(
    question: str,
    results: list[dict[str, Any]],
    *,
    intent: str | None = None,
    sql_source: str = "canned",
    use_llm: bool | None = None,
) -> str:
    """
    Produce a natural-language answer from query results.

    Canned intents keep template answers. Generated SQL uses the
    deterministic renderer, with an optional LLM phrasing pass when
    the app is in LLM planner mode.
    """

    canned = (
        sql_source != "generated"
        and sql_source != "repaired"
        and intent in VALID_INTENTS
    )
    if canned:
        return generate_response(intent, results)

    settings = get_settings()
    allow_llm = (
        use_llm if use_llm is not None else settings.query_planner_mode == "llm"
    )
    if allow_llm:
        phrased = _llm_interpret(question, results)
        if phrased:
            return phrased

    return render_rows(question, results)


__all__ = [
    "interpret_results",
    "render_rows",
]
