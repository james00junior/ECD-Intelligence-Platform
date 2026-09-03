"""Benchmark the production internal-knowledge retrieval path."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.database.database import SessionLocal
from app.tools.internal_knowledge_tool import search_internal_knowledge

from .metrics import aggregate_metrics, recall_at_k, reciprocal_rank

DEFAULT_DATASET = Path(__file__).with_name("dataset.json")


def load_dataset(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list) or not data:
        raise ValueError(f"Evaluation dataset must be a non-empty JSON list: {path}")

    return data


def _source_uri(evidence: dict) -> str | None:
    provenance = evidence.get("provenance") or {}
    uri = provenance.get("uri")
    return uri if isinstance(uri, str) and uri else None


def _title(evidence: dict) -> str:
    provenance = evidence.get("provenance") or {}
    title = provenance.get("title")
    return title if isinstance(title, str) else "Unknown document"


def _score(evidence: dict) -> float | None:
    score = evidence.get("score")
    try:
        return float(score) if score is not None else None
    except (TypeError, ValueError):
        return None


def evaluate_case(case: dict, db) -> dict:
    question = case["question"]
    organisation_id = int(case["organisation_id"])
    relevant = set(case["expected_source_uris"])

    started = time.perf_counter()

    evidence = search_internal_knowledge(
        question=question,
        organisation_id=organisation_id,
        db=db,
        limit=5,
    )

    latency_ms = (time.perf_counter() - started) * 1000

    retrieved = [
        uri
        for uri in (_source_uri(item) for item in evidence)
        if uri
    ]

    retrieved_unique = list(dict.fromkeys(retrieved))

    result = {
        "id": case["id"],
        "question": question,
        "retrieved_source_uris": retrieved_unique,
        "expected_source_uris": sorted(relevant),
        "recall_at_1": recall_at_k(retrieved_unique, relevant, 1),
        "recall_at_3": recall_at_k(retrieved_unique, relevant, 3),
        "recall_at_5": recall_at_k(retrieved_unique, relevant, 5),
        "mrr": reciprocal_rank(retrieved_unique, relevant),
        "latency_ms": latency_ms,
    }

    print()
    print("=" * 80)
    print(f"{case['id']}: {question}")
    print("-" * 80)

    print("Expected:")
    for uri in sorted(relevant):
        print(f"  ✓ {uri}")

    print("\nRetrieved top-5:")
    for rank, item in enumerate(evidence, start=1):
        uri = _source_uri(item)
        title = _title(item)
        score = _score(item)

        score_text = f"{score:.4f}" if score is not None else "n/a"
        hit = "✓ EXPECTED" if uri in relevant else "✗"

        print(f"  {rank}. [{score_text}] {hit}")
        print(f"     {title}")
        print(f"     {uri}")

    print("-" * 80)
    print(
        f"R@1={result['recall_at_1']:.0f} "
        f"R@3={result['recall_at_3']:.0f} "
        f"R@5={result['recall_at_5']:.0f} "
        f"MRR={result['mrr']:.3f} "
        f"latency={result['latency_ms']:.1f}ms"
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate internal RAG retrieval."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    results: list[dict] = []

    with SessionLocal() as db:
        for case in dataset:
            result = evaluate_case(case, db)
            results.append(result)

    summary = aggregate_metrics(results)

    print()
    print("=" * 80)
    print("RAG retrieval baseline")
    print("=" * 80)
    print(f"Queries:       {len(results)}")
    print(f"Recall@1:      {summary['recall_at_1']:.3f}")
    print(f"Recall@3:      {summary['recall_at_3']:.3f}")
    print(f"Recall@5:      {summary['recall_at_5']:.3f}")
    print(f"MRR:           {summary['mrr']:.3f}")
    print(f"Mean latency:  {summary['mean_latency_ms']:.1f} ms")

    payload = {
        "summary": summary,
        "results": results,
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()