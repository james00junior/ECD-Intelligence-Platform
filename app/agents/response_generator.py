"""
Response generator for the ECD intelligence platform.

This module converts structured analytics results into
human-readable answers.
"""

from __future__ import annotations

from typing import Any


def _format_number(value: Any) -> str:
    """Format numeric values for human-readable responses."""

    if value is None:
        return "0"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return f"{value:,.0f}"

    return str(value)


def _format_grouped_results(
    results: list[dict[str, Any]],
    group_key: str,
    value_key: str,
    title: str,
) -> str:
    """Format grouped analytics results."""

    if not results:
        return f"No {title.lower()} were found."

    lines = [title]

    for row in results:
        group_value = row.get(group_key, "Unknown")
        value = _format_number(row.get(value_key, 0))

        lines.append(f"- {group_value}: {value}")

    return "\n".join(lines)


def generate_response(
    intent: str | None,
    results: list[dict[str, Any]],
) -> str:
    """
    Generate a human-readable answer from an analytics intent
    and structured query results.
    """

    if not intent:
        return "I could not determine how to answer that question."

    if not results:
        return "No results were found."

    # ---------------------------------------------------------
    # TOTAL FRANCHISEES
    # ---------------------------------------------------------

    if intent == "count_franchisees":

        count = _format_number(
            results[0].get("franchisee_count", 0)
        )

        return f"There are currently {count} franchisees."

    # ---------------------------------------------------------
    # ACTIVE FRANCHISEES
    # ---------------------------------------------------------

    if intent == "active_franchisees":

        count = _format_number(
            results[0].get("active_franchisee_count", 0)
        )

        return (
            f"There are currently {count} active franchisees."
        )

    # ---------------------------------------------------------
    # ENROLLED CHILDREN
    # ---------------------------------------------------------

    if intent == "count_children":

        count = _format_number(
            results[0].get("child_count", 0)
        )

        return (
            f"There are currently {count} enrolled children."
        )

    # ---------------------------------------------------------
    # FRANCHISEES BY STATUS
    # ---------------------------------------------------------

    if intent == "franchisees_by_status":

        return _format_grouped_results(
            results=results,
            group_key="status",
            value_key="franchisee_count",
            title="Franchisees by status:",
        )

    # ---------------------------------------------------------
    # FRANCHISEES BY PROVINCE
    # ---------------------------------------------------------

    if intent == "franchisees_by_province":

        return _format_grouped_results(
            results=results,
            group_key="province",
            value_key="franchisee_count",
            title="Franchisees by province:",
        )

    # ---------------------------------------------------------
    # FRANCHISEES BY MAIN PLACE
    # ---------------------------------------------------------

    if intent == "franchisees_by_main_place":

        return _format_grouped_results(
            results=results,
            group_key="main_place",
            value_key="franchisee_count",
            title="Franchisees by main place:",
        )

    # ---------------------------------------------------------
    # CHILDREN BY PROVINCE
    # ---------------------------------------------------------

    if intent == "children_by_province":

        return _format_grouped_results(
            results=results,
            group_key="province",
            value_key="child_count",
            title="Enrolled children by province:",
        )

    # ---------------------------------------------------------
    # POPULATION BY PROVINCE
    # ---------------------------------------------------------

    if intent == "population_by_province":

        return _format_grouped_results(
            results=results,
            group_key="province",
            value_key="population",
            title="Population by province:",
        )

    return "The query was completed successfully."


__all__ = [
    "generate_response",
]