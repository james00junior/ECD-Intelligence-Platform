"""Evidence selection, conflict detection, and tenant-boundary enforcement."""

from __future__ import annotations

from typing import Any


def _evidence_key(evidence: dict[str, Any]) -> tuple[str, str, str]:
    provenance = evidence["provenance"]
    return (
        provenance["source_type"],
        provenance["source_id"],
        " ".join(evidence["content"].lower().split()),
    )


def _rank(evidence: dict[str, Any]) -> float:
    score = evidence.get("score")
    if isinstance(score, (int, float)):
        return float(score)
    return {"sql": 1.0, "internal_document": 0.5, "external": 0.25}.get(
        evidence["provenance"]["source_type"], 0.0
    )


def aggregate_evidence(
    evidence_items: list[dict[str, Any]], organisation_id: int | None
) -> dict[str, Any]:
    """Return deduplicated, ranked evidence and explicit conflict records."""

    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for evidence in evidence_items:
        provenance = evidence.get("provenance")
        if not isinstance(provenance, dict) or not evidence.get("content"):
            rejected.append(evidence)
            continue
        source_type = provenance.get("source_type")
        source_organisation_id = provenance.get("organisation_id")
        tenant_safe = (
            source_type == "external" and source_organisation_id is None
        ) or (
            source_type in {"sql", "internal_document"}
            and organisation_id is not None
            and source_organisation_id == organisation_id
        )
        if not tenant_safe:
            rejected.append(evidence)
            continue
        key = _evidence_key(evidence)
        if key in seen:
            rejected.append(evidence)
            continue
        seen.add(key)
        selected.append(evidence)
    selected.sort(key=_rank, reverse=True)

    claims: dict[str, list[dict[str, Any]]] = {}
    for evidence in selected:
        claim_key = evidence.get("metadata", {}).get("claim_key")
        if isinstance(claim_key, str) and claim_key:
            claims.setdefault(claim_key, []).append(evidence)
    conflicts = []
    for claim_key, claim_evidence in claims.items():
        if len({item["content"] for item in claim_evidence}) > 1:
            conflicts.append({
                "claim_key": claim_key,
                "evidence_ids": [item["evidence_id"] for item in claim_evidence],
            })
    return {
        "selected_evidence": selected,
        "rejected_evidence": rejected,
        "conflicts": conflicts,
    }


__all__ = ["aggregate_evidence"]
