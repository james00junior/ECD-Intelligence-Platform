"""
Grounded, source-aware synthesis for Research Agent evidence.

SQL facts are rendered deterministically so database values cannot
be changed by an LLM.

Document and external evidence are summarized by the configured LLM
into a concise, source-grounded answer.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.response_generator import generate_response
from app.services.llm_provider import complete_text
from app.services.query_planner import VALID_INTENTS


def build_synthesis_prompt(
    question: str,
    evidence: list[dict[str, Any]],
) -> str:
    """
    Build a grounded synthesis prompt from selected evidence only.
    """

    sources: list[str] = []

    for index, item in enumerate(evidence, start=1):
        provenance = item.get("provenance", {})

        source_type = provenance.get(
            "source_type",
            "unknown",
        )
        title = provenance.get(
            "title",
            "Untitled source",
        )
        content = str(
            item.get("content", "")
        ).strip()

        if not content:
            continue

        sources.append(
            f"[{index}] {source_type} | {title}\n"
            f"{content}"
        )

    return (
        "You are the grounded synthesis layer of an enterprise "
        "ECD intelligence platform.\n\n"
        "Answer the user's question using ONLY the supplied evidence.\n"
        "Do not invent facts, numbers, dates, organisations, or claims.\n"
        "Do not change or estimate numerical values from SQL evidence.\n"
        "Do not mention evidence that does not support the answer.\n"
        "Do not reproduce raw JSON, database rows, or document chunks.\n"
        "Synthesize the evidence into concise, natural language.\n"
        "Cite factual claims using the supplied bracketed source numbers.\n"
        "If the evidence does not support part of the question, say so.\n\n"
        f"Question:\n{question.strip()}\n\n"
        "Evidence:\n"
        + "\n\n".join(sources)
    )


def _parse_sql_evidence(
    item: dict[str, Any],
) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Convert SQL evidence content back into structured rows.
    """

    provenance = item.get("provenance", {})
    metadata = provenance.get("metadata", {})
    intent = metadata.get("intent")

    if intent not in VALID_INTENTS:
        return None, []

    try:
        rows = json.loads(
            item.get("content", "[]")
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
    Render known SQL evidence using deterministic response templates.
    """

    facts: list[str] = []
    references: list[int] = []

    for index, item in enumerate(evidence, start=1):
        provenance = item.get("provenance", {})

        if provenance.get("source_type") != "sql":
            continue

        intent, rows = _parse_sql_evidence(item)

        if not intent or not rows:
            continue

        rendered = generate_response(
            intent,
            rows,
        )

        if (
            rendered
            and rendered != "The query was completed successfully."
        ):
            facts.append(rendered)
            references.append(index)

    return facts, references


def _document_evidence(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return document/external evidence for LLM synthesis.

    SQL evidence is deliberately excluded because SQL facts are
    rendered deterministically.
    """

    return [
        item
        for item in evidence
        if item.get("provenance", {}).get("source_type")
        in {
            "internal_document",
            "external",
        }
    ]


def _synthesize_document_evidence(
    question: str,
    evidence: list[dict[str, Any]],
) -> str | None:
    """
    Ask the configured LLM to synthesize document/external evidence.

    This layer is strictly grounded in the supplied evidence.
    """

    document_evidence = _document_evidence(evidence)

    if not document_evidence:
        return None

    prompt = build_synthesis_prompt(
        question,
        document_evidence,
    )

    try:
        result = complete_text(prompt)
    except Exception:
        return None

    if result is None:
        return None

    answer = result.text.strip()

    if not answer:
        return None

    return answer


def _deterministic_document_fallback(
    evidence: list[dict[str, Any]],
) -> str | None:
    """
    Safe fallback when the LLM is unavailable.

    We deliberately do not dump complete document chunks into the
    answer. Instead, provide a concise source-level availability
    statement.
    """

    document_evidence = _document_evidence(evidence)

    if not document_evidence:
        return None

    titles: list[str] = []

    for item in document_evidence:
        title = str(
            item.get("provenance", {}).get(
                "title",
                "",
            )
        ).strip()

        if title and title not in titles:
            titles.append(title)

    if not titles:
        return (
            "Relevant organisational or external evidence was found, "
            "but it could not be summarized automatically."
        )

    if len(titles) == 1:
        return (
            f"Relevant evidence was found in "
            f"“{titles[0]}”, but it could not be summarized "
            "automatically."
        )

    return (
        "Relevant evidence was found in the following sources, "
        "but it could not be summarized automatically: "
        + ", ".join(f"“{title}”" for title in titles)
        + "."
    )


def _build_citations(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build platform citations while preserving source identity.
    """

    citations: list[dict[str, Any]] = []

    for index, item in enumerate(evidence, start=1):
        provenance = item.get("provenance", {})

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
                "source_type": provenance.get(
                    "source_type"
                ),
                "source_kind": source_kind,
                "title": provenance.get(
                    "title"
                ),
                "uri": provenance.get(
                    "uri"
                ),
                "source_id": provenance.get(
                    "source_id"
                ),
            }
        )

    return citations


def synthesize_grounded_answer(
    question: str,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a coherent, grounded answer from selected evidence.

    SQL facts are always rendered deterministically.

    Internal and external evidence are summarized by the configured
    LLM, with a safe fallback when the LLM is unavailable.
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

    sql_facts, sql_refs = _render_sql_evidence(
        evidence
    )

    document_answer = _synthesize_document_evidence(
        question,
        evidence,
    )

    if document_answer is None:
        document_answer = _deterministic_document_fallback(
            evidence
        )

    answer_sections: list[str] = []

    # ---------------------------------------------------------------
    # SQL / OPERATIONAL FACTS
    # ---------------------------------------------------------------

    for fact, reference in zip(
        sql_facts,
        sql_refs,
    ):
        answer_sections.append(
            f"{fact} [{reference}]"
        )

    # ---------------------------------------------------------------
    # DOCUMENT / EXTERNAL SYNTHESIS
    # ---------------------------------------------------------------

    if document_answer:
        answer_sections.append(
            document_answer
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