"""RAG metric unit tests."""

from evals.rag.metrics import aggregate_metrics, recall_at_k, reciprocal_rank


def test_recall_at_k_deduplicates_results():
    retrieved = ["doc-a", "doc-a", "doc-b"]
    relevant = {"doc-b"}

    assert recall_at_k(retrieved, relevant, 1) == 0.0
    assert recall_at_k(retrieved, relevant, 2) == 1.0


def test_reciprocal_rank_uses_first_relevant_document():
    assert reciprocal_rank(["doc-a", "doc-b", "doc-c"], {"doc-b"}) == 0.5
    assert reciprocal_rank(["doc-a", "doc-a"], {"doc-b"}) == 0.0


def test_aggregate_metrics():
    results = [
        {
            "recall_at_1": 1.0,
            "recall_at_3": 1.0,
            "recall_at_5": 1.0,
            "mrr": 1.0,
            "latency_ms": 10.0,
        },
        {
            "recall_at_1": 0.0,
            "recall_at_3": 1.0,
            "recall_at_5": 1.0,
            "mrr": 0.5,
            "latency_ms": 30.0,
        },
    ]

    assert aggregate_metrics(results) == {
        "recall_at_1": 0.5,
        "recall_at_3": 1.0,
        "recall_at_5": 1.0,
        "mrr": 0.75,
        "mean_latency_ms": 20.0,
    }
