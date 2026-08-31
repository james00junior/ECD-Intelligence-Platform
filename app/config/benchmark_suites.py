"""
Benchmark question suites for LLM query planner evaluation.

Each case is (question, expected_intent).
``None`` means the question should be classified as unsupported.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    question: str
    expected_intent: str | None
    category: str
    notes: str = ""


STANDARD_SUITE: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        "How many franchisees are there?",
        "count_franchisees",
        "supported",
    ),
    BenchmarkCase(
        "How many active franchisees are there?",
        "active_franchisees",
        "supported",
    ),
    BenchmarkCase(
        "How many children are enrolled?",
        "count_children",
        "supported",
    ),
    BenchmarkCase(
        "How many franchisees are there by status?",
        "franchisees_by_status",
        "supported",
    ),
    BenchmarkCase(
        "How many franchisees are there by province?",
        "franchisees_by_province",
        "supported",
    ),
    BenchmarkCase(
        "How many enrolled children are there by province?",
        "children_by_province",
        "supported",
    ),
    BenchmarkCase(
        "What is the population by province?",
        "population_by_province",
        "supported",
    ),
    BenchmarkCase(
        "What is the weather in Johannesburg?",
        None,
        "unsupported",
        "Outside analytics domain",
    ),
)


EXTENDED_SUITE: tuple[BenchmarkCase, ...] = STANDARD_SUITE + (
    # User-provided questions
    BenchmarkCase(
        "How many organisations are in the system?",
        None,
        "advanced",
        "No organisation-count intent exists yet",
    ),
    BenchmarkCase(
        "How many franchisees do we have?",
        "count_franchisees",
        "paraphrase",
    ),
    BenchmarkCase(
        "How many children are enrolled?",
        "count_children",
        "paraphrase",
    ),
    BenchmarkCase(
        "Which province has the most franchisees?",
        None,
        "advanced",
        "Requires ranking/max, not just group-by",
    ),
    BenchmarkCase(
        "How many franchisees does each coach manage?",
        None,
        "advanced",
        "No coach dimension intent exists yet",
    ),
    # Additional advanced / edge cases
    BenchmarkCase(
        "Show me franchisees grouped by main place",
        "franchisees_by_main_place",
        "paraphrase",
    ),
    BenchmarkCase(
        "What is the average attendance rate across all franchisees?",
        None,
        "advanced",
        "No attendance aggregate intent",
    ),
    BenchmarkCase(
        "Which franchisees are operating below 50% capacity?",
        None,
        "advanced",
        "No capacity filter intent",
    ),
    BenchmarkCase(
        "How many new children enrolled last month?",
        None,
        "advanced",
        "No time-filtered enrolment intent",
    ),
    BenchmarkCase(
        "Compare active versus inactive franchisees",
        "franchisees_by_status",
        "paraphrase",
    ),
    BenchmarkCase(
        "Total enrolled children per province",
        "children_by_province",
        "paraphrase",
    ),
    BenchmarkCase(
        "Give me a breakdown of franchisees by province and status",
        None,
        "advanced",
        "Multi-dimensional query not supported",
    ),
    BenchmarkCase(
        "Who is the top performing coach by franchisee count?",
        None,
        "advanced",
        "Ranking by coach not supported",
    ),
)


SUITES: dict[str, tuple[BenchmarkCase, ...]] = {
    "standard": STANDARD_SUITE,
    "extended": EXTENDED_SUITE,
}


__all__ = [
    "BenchmarkCase",
    "EXTENDED_SUITE",
    "STANDARD_SUITE",
    "SUITES",
]
