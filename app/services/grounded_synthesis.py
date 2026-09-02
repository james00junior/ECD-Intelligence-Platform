"""
Grounded, source-aware synthesis for Research Agent evidence.

Known SQL facts are rendered deterministically so database values
cannot be altered by an LLM.

Internal document evidence is preserved and presented alongside
the operational analytics rather than being discarded.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.response_generator import generate_response
from app.services.query_planner import VALID_INTENTS


def build_synthesis_prompt(
    question: str,
    evidence: list[dict[str, Any]],
) -> str:
    """
    Build a source-only prompt for a future LLM synthesis layer.
    """

    sources = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        provenance = item["provenance"]

        sources.append(
            f"[{index}] "
            f"{provenance['source_type']} | "
            f"{provenance['title']}\n"
            f"{item['content']}"
        )

    return (
        "Answer only from the supplied evidence. "
        "Do not invent facts or numbers. "
        "Cite factual claims using bracketed source numbers.\n\n"
        f"Question: {question}\n\n"
        "Evidence:\n"
        + "\n\n".join(sources)
    )


def _parse_sql_evidence(
    item: dict[str, Any],
) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Convert SQL evidence back into structured rows.
    """

    provenance = item.get(
        "provenance",
        {},
    )

    metadata = provenance.get(
        "metadata",
        {},
    )

    intent = metadata.get("intent")

    if intent not in VALID_INTENTS:
        return None, []

    try:
        rows = json.loads(
            item.get(
                "content",
                "[]",
            )
        )

    except (
        TypeError,
        json.JSONDecodeError,
    ):
        return intent, []

    if not isinstance(rows, list):
        return intent, []

    return (
        intent,
        [
            row
            for row in rows
            if isinstance(row, dict)
        ],
    )


def _render_sql_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[list[str], list[int]]:
    """
    Render known SQL evidence as human-readable facts.
    """

    facts: list[str] = []
    references: list[int] = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        provenance = item.get(
            "provenance",
            {},
        )

        if provenance.get(
            "source_type"
        ) != "sql":
            continue

        intent, rows = _parse_sql_evidence(
            item
        )

        if not intent or not rows:
            continue

        rendered = generate_response(
            intent,
            rows,
        )

        if (
            rendered
            and rendered
            != "The query was completed successfully."
        ):
            facts.append(rendered)
            references.append(index)

    return facts, references


def _render_internal_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[list[str], list[int]]:
    """
    Preserve internal-document findings.

    Each finding remains linked to its source so the final
    answer can provide transparent provenance.
    """

    findings: list[str] = []
    references: list[int] = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        provenance = item.get(
            "provenance",
            {},
        )

        if (
            provenance.get(
                "source_type"
            )
            != "internal_document"
        ):
            continue

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        findings.append(content)
        references.append(index)

    return findings, references


def _render_external_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[list[str], list[int]]:
    """
    Preserve external research evidence.
    """

    findings: list[str] = []
    references: list[int] = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        provenance = item.get(
            "provenance",
            {},
        )

        if (
            provenance.get(
                "source_type"
            )
            != "external"
        ):
            continue

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        findings.append(content)
        references.append(index)

    return findings, references


def _build_citations(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build platform citations while preserving source identity.
    """

    citations = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):

        provenance = item["provenance"]

        organisation_id = provenance.get(
            "organisation_id"
        )

        source_kind = (
            "organisational"
            if organisation_id is not None
            else "external"
        )

        citations.append(
            {
                "reference": index,
                "source_type": provenance[
                    "source_type"
                ],
                "source_kind": source_kind,
                "title": provenance[
                    "title"
                ],
                "uri": provenance.get(
                    "uri"
                ),
                "source_id": provenance[
                    "source_id"
                ],
            }
        )

    return citations


def synthesize_grounded_answer(
    question: str,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a coherent answer from multiple evidence sources.

    SQL analytics are rendered deterministically.

    Internal and external research are preserved instead of
    being discarded when SQL evidence is present.
    """

    if not evidence:
        return {
            "answer": None,
            "citations": [],
            "error": (
                "Insufficient evidence to answer "
                "the question."
            ),
        }

    sql_facts, sql_refs = (
        _render_sql_evidence(
            evidence
        )
    )

    internal_findings, internal_refs = (
        _render_internal_evidence(
            evidence
        )
    )

    external_findings, external_refs = (
        _render_external_evidence(
            evidence
        )
    )

    answer_sections: list[str] = []

    # ---------------------------------------------------------------
    # OPERATIONAL DATA
    # ---------------------------------------------------------------

    if sql_facts:

        answer_sections.append(
            "### Operational data\n"
            + "\n".join(
                f"- {fact} [{reference}]"
                for fact, reference in zip(
                    sql_facts,
                    sql_refs,
                )
            )
        )

    # ---------------------------------------------------------------
    # INTERNAL PROGRAMME INTELLIGENCE
    # ---------------------------------------------------------------

    if internal_findings:

        answer_sections.append(
            "### Programme intelligence\n"
            + "\n".join(
                f"- {finding} [{reference}]"
                for finding, reference in zip(
                    internal_findings,
                    internal_refs,
                )
            )
        )

    # ---------------------------------------------------------------
    # EXTERNAL RESEARCH
    # ---------------------------------------------------------------

    if external_findings:

        answer_sections.append(
            "### External research\n"
            + "\n".join(
                f"- {finding} [{reference}]"
                for finding, reference in zip(
                    external_findings,
                    external_refs,
                )
            )
        )

    if not answer_sections:

        return {
            "answer": None,
            "citations": _build_citations(
                evidence
            ),
            "error": (
                "The available evidence could "
                "not be rendered."
            ),
        }

    return {
        "answer": "\n\n".join(
            answer_sections
        ),
        "citations": _build_citations(
            evidence
        ),
        "error": None,
    }


__all__ = [
    "build_synthesis_prompt",
    "synthesize_grounded_answer",
]