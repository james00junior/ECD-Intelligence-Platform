"""Organisation-scoped internal knowledge retrieval for the Research Agent."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.orm import Session

from app.services.embedding_service import embed_text
from app.services.vector_service import search_similar_chunks


_TRACKING_QUERY_PREFIXES = (
    "utm_",
    "mc_",
    "fbclid",
    "gclid",
)


def canonicalize_source_uri(uri: str | None) -> str | None:
    """Return a stable canonical representation of a source URI.

    Canonicalisation removes URL fragments, normalises scheme/host casing,
    removes trailing slashes from non-root paths, and removes common
    tracking parameters while preserving meaningful query parameters.
    """
    if not isinstance(uri, str) or not uri.strip():
        return None

    uri = uri.strip()
    parsed = urlsplit(uri)

    # Handle non-URL identifiers such as document://quality-report.
    if not parsed.scheme or not parsed.netloc:
        return uri.rstrip("/") or uri

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/")

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not (
            key.lower().startswith(_TRACKING_QUERY_PREFIXES)
            or key.lower() in _TRACKING_QUERY_PREFIXES
        )
    ]

    query = urlencode(query_pairs, doseq=True)

    # Fragments identify locations within the same source document.
    return urlunsplit((scheme, netloc, path, query, ""))


def _deduplication_key(chunk: dict[str, Any]) -> tuple[Any, ...]:
    """Build the identity key used to remove exact duplicate evidence.

    Two chunks are considered exact duplicates when they belong to the same
    document, point to the same canonical source URI, and contain the same
    content hash. chunk_id is deliberately excluded because duplicated rows
    can have different database IDs.
    """
    document_id = chunk.get("document_id")
    source_uri = canonicalize_source_uri(chunk.get("source_uri"))
    content_hash = chunk.get("content_hash")

    return (
        document_id,
        source_uri,
        content_hash,
    )


def _deduplicate_chunks(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove exact duplicate chunks while preserving retrieval order.

    Distinct chunks from the same document are retained as long as their
    content hashes differ.
    """
    seen: set[tuple[Any, ...]] = set()
    deduplicated: list[dict[str, Any]] = []

    for chunk in chunks:
        key = _deduplication_key(chunk)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(chunk)

    return deduplicated


def select_diverse_chunks(
    chunks: list[dict[str, Any]],
    limit: int,
    diversity_threshold: float = 0.05,
) -> list[dict[str, Any]]:
    """Select relevant evidence while encouraging document diversity.

    The highest-scoring candidate is selected first. For subsequent
    selections, a chunk from a new document is preferred when its similarity
    score is within ``diversity_threshold`` of the best remaining candidate.
    This prevents one document from dominating the evidence set while still
    allowing multiple highly relevant chunks from the same document.
    """
    if limit <= 0 or not chunks:
        return []

    selected: list[dict[str, Any]] = []
    remaining = list(chunks)
    selected_documents: set[Any] = set()

    while remaining and len(selected) < limit:
        best = remaining[0]
        best_score = float(best.get("similarity") or 0.0)

        diverse_candidate = next(
            (
                chunk
                for chunk in remaining
                if chunk.get("document_id") not in selected_documents
                and (
                    best_score
                    - float(chunk.get("similarity") or 0.0)
                    <= diversity_threshold
                )
            ),
            None,
        )

        candidate = diverse_candidate or best
        selected.append(candidate)

        document_id = candidate.get("document_id")
        if document_id is not None:
            selected_documents.add(document_id)

        remaining.remove(candidate)

    return selected


def search_internal_knowledge(
    question: str,
    organisation_id: int,
    db: Session,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve organisation-scoped internal knowledge evidence.

    Retrieval is performed using the configured embedding model and pgvector.
    Results are then filtered, deduplicated, diversified, and converted into
    the evidence format consumed by the Research Agent.
    """
    if not question or not question.strip():
        raise ValueError("question must not be empty")

    if organisation_id <= 0:
        raise ValueError("organisation_id must be positive")

    if limit <= 0:
        return []

    query_embedding = embed_text(question).embedding

    chunks = search_similar_chunks(
        db=db,
        organisation_id=organisation_id,
        query_embedding=query_embedding,
        limit=limit,
    )

    # Defence in depth: vector search is organisation-scoped, but enforce the
    # boundary again before evidence leaves this tool.
    chunks = [
        chunk
        for chunk in chunks
        if chunk.get("organisation_id") == organisation_id
    ]

    # Step 1: remove exact duplicate chunks.
    chunks = _deduplicate_chunks(chunks)

    # Step 2: encourage evidence diversity across documents.
    chunks = select_diverse_chunks(
        chunks,
        limit=limit,
    )

    evidence: list[dict[str, Any]] = []

    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        document_id = chunk["document_id"]
        metadata = chunk.get("metadata") or {}

        evidence.append(
            {
                "evidence_id": f"document-chunk:{chunk_id}",
                "content": chunk["content"],
                "provenance": {
                    "source_type": "internal_document",
                    "source_id": f"document:{document_id}",
                    "title": chunk.get("title"),
                    "uri": canonicalize_source_uri(chunk.get("source_uri")),
                    "organisation_id": organisation_id,
                    "metadata": {
                        **metadata,
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk.get("chunk_index"),
                    },
                },
                "score": chunk.get("similarity"),
                "metadata": {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk.get("chunk_index"),
                },
            }
        )

    return evidence


__all__ = [
    "canonicalize_source_uri",
    "search_internal_knowledge",
    "select_diverse_chunks",
]
