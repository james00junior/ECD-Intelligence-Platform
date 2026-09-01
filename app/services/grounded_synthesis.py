"""Deterministic, citation-backed synthesis for selected research evidence."""

from __future__ import annotations

from typing import Any


def build_synthesis_prompt(question: str, evidence: list[dict[str, Any]]) -> str:
    """Build a source-only prompt for a future answer-model adapter."""

    sources = []
    for index, item in enumerate(evidence, start=1):
        provenance = item["provenance"]
        sources.append(
            f"[{index}] {provenance['source_type']} | "
            f"{provenance['title']}\n{item['content']}"
        )
    return (
        "Answer only from the supplied evidence. Cite every factual claim "
        "using its bracketed source number. If evidence is insufficient, say so.\n\n"
        f"Question: {question}\n\nEvidence:\n" + "\n\n".join(sources)
    )


def synthesize_grounded_answer(
    question: str, evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    """Create an evidence-only answer with platform-generated citations."""

    if not evidence:
        return {
            "answer": None,
            "citations": [],
            "error": "Insufficient evidence to answer the question.",
        }
    _ = build_synthesis_prompt(question, evidence)
    answer_lines = ["Based on the available evidence:"]
    citations = []
    for index, item in enumerate(evidence, start=1):
        provenance = item["provenance"]
        source_kind = (
            "organisational" if provenance["organisation_id"] is not None
            else "external"
        )
        answer_lines.append(f"- {item['content']} [{index}]")
        citations.append({
            "reference": index,
            "source_type": provenance["source_type"],
            "source_kind": source_kind,
            "title": provenance["title"],
            "uri": provenance["uri"],
            "source_id": provenance["source_id"],
        })
    return {
        "answer": "\n".join(answer_lines),
        "citations": citations,
        "error": None,
    }


__all__ = ["build_synthesis_prompt", "synthesize_grounded_answer"]
