"""Bounded retry policy for the Research Agent."""

from __future__ import annotations

from typing import Any


DEFAULT_MAX_RESEARCH_STEPS = 6


def evaluate_evidence_sufficiency(
    evidence: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    error: str | None,
    research_steps: int,
    max_research_steps: int,
    has_retrieval_source: bool,
) -> dict[str, Any]:
    """Decide whether evidence is safe to synthesize or warrants one retry."""

    if conflicts:
        return {"sufficient": False, "should_retry": False, "reason": "Conflicting evidence requires review."}
    if evidence:
        return {"sufficient": True, "should_retry": False, "reason": None}
    if error:
        return {"sufficient": False, "should_retry": False, "reason": error}
    if not has_retrieval_source:
        return {"sufficient": False, "should_retry": False, "reason": "No research source was selected for this question."}
    if research_steps >= max_research_steps:
        return {"sufficient": False, "should_retry": False, "reason": "Research step limit reached without sufficient evidence."}
    return {"sufficient": False, "should_retry": True, "reason": "No evidence was retrieved; retry with a refined query."}


def refine_research_query(question: str, attempt: int) -> str:
    """Create a deterministic, auditable follow-up retrieval query."""

    if attempt < 1:
        return question
    return f"{question.strip()} Provide concrete supporting evidence."


__all__ = ["DEFAULT_MAX_RESEARCH_STEPS", "evaluate_evidence_sufficiency", "refine_research_query"]
