from __future__ import annotations


PROVINCES = (
    "gauteng",
    "western cape",
    "eastern cape",
    "kwazulu-natal",
    "kwazulu natal",
    "kzn",
    "free state",
    "limpopo",
    "mpumalanga",
    "north west",
    "northern cape",
)


def classify_intent(question: str) -> str | None:
    """
    Classify a natural-language analytics question.
    """

    if not isinstance(question, str):
        return None

    q = question.lower().strip()

    if not q:
        return None

    # ---------------------------------------------------------------
    # SPECIFIC PROVINCE QUESTIONS
    # ---------------------------------------------------------------

    if (
        "franchisee" in q
        and any(province in q for province in PROVINCES)
        and any(
            phrase in q
            for phrase in [
                "how many",
                "count",
                "number",
                "total",
                "operating",
                "located",
            ]
        )
    ):
        return "franchisees_in_province"

    # ---------------------------------------------------------------
    # GROUPED QUESTIONS
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # ACTIVE FRANCHISEES
    # ---------------------------------------------------------------

    if (
        "active franchisee" in q
        or (
            "franchisee" in q
            and "active" in q
        )
    ):
        return "active_franchisees"

    # ---------------------------------------------------------------
    # CHILDREN
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # TOTAL FRANCHISEES
    # ---------------------------------------------------------------

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


__all__ = [
    "PROVINCES",
    "classify_intent",
]