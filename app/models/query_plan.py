from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsPlan:
    """Structured analytics query plan derived from a classified intent."""

    intent: str
    entity: str
    measure: str
    dimension: str | None


# Backward-compatible alias for workflow code referencing QueryPlan.
QueryPlan = AnalyticsPlan


__all__ = [
    "AnalyticsPlan",
    "QueryPlan",
]
