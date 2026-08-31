from __future__ import annotations


def classify_intent(question: str) -> str | None:
    """
    Classify a natural-language analytics question.
    """

    if not isinstance(question, str):
        return None

    q = question.lower().strip()

    if not q:
        return None

    # Specific grouped questions must come first.

    if (
        "franchisee" in q
        and "province" in q
        and ("by" in q or "per" in q or "each" in q)
    ):
        return "franchisees_by_province"

    if (
        "franchisee" in q
        and "main place" in q
        and ("by" in q or "per" in q or "each" in q)
    ):
        return "franchisees_by_main_place"

    if (
        ("children" in q or "child" in q)
        and "province" in q
        and ("by" in q or "per" in q or "each" in q)
    ):
        return "children_by_province"

    if (
        "population" in q
        and "province" in q
        and ("by" in q or "per" in q or "each" in q)
    ):
        return "population_by_province"

    if (
        "franchisee" in q
        and "status" in q
        and ("by" in q or "per" in q or "each" in q)
    ):
        return "franchisees_by_status"

    if (
        "active franchisee" in q
        or (
            "franchisee" in q
            and "active" in q
        )
    ):
        return "active_franchisees"

    if (
        ("children" in q or "child" in q)
        and any(
            phrase in q
            for phrase in [
                "how many",
                "count",
                "number",
                "total",
                "enrolled",
            ]
        )
    ):
        return "count_children"

    if (
        "franchisee" in q
        and any(
            phrase in q
            for phrase in [
                "how many",
                "count",
                "number",
                "total",
            ]
        )
    ):
        return "count_franchisees"

    return None
