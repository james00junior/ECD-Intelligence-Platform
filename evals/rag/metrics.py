"""Metrics for document-level retrieval evaluation."""

from __future__ import annotations

from collections.abc import Sequence


def _unique_in_order(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Return binary Recall@k for one query."""
    if k <= 0 or not relevant:
        return 0.0
    ranked = _unique_in_order(retrieved)[:k]
    return 1.0 if any(item in relevant for item in ranked) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: set[str]) -> float:
    """Return reciprocal rank of the first relevant result."""
    if not relevant:
        return 0.0
    for rank, item in enumerate(_unique_in_order(retrieved), start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def mean(values: Sequence[float]) -> float:
    """Return the arithmetic mean, or zero for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def aggregate_metrics(results: Sequence[dict]) -> dict[str, float]:
    """Aggregate per-query retrieval metrics."""
    return {
        "recall_at_1": mean([float(r["recall_at_1"]) for r in results]),
        "recall_at_3": mean([float(r["recall_at_3"]) for r in results]),
        "recall_at_5": mean([float(r["recall_at_5"]) for r in results]),
        "mrr": mean([float(r["mrr"]) for r in results]),
        "mean_latency_ms": mean([float(r["latency_ms"]) for r in results]),
    }


__all__ = ["aggregate_metrics", "mean", "recall_at_k", "reciprocal_rank"]
