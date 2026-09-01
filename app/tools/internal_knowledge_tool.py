"""Organisation-scoped internal knowledge retrieval for the Research Agent."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.embedding_service import embed_text
from app.services.vector_service import search_similar_chunks


def search_internal_knowledge(
    question: str,
    organisation_id: int,
    db: Session,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve document evidence for one organisation only."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")
    if not isinstance(organisation_id, int) or organisation_id < 1:
        raise ValueError("A valid organisation_id is required.")

    query_embedding = embed_text(question).embedding
    chunks = search_similar_chunks(
        db=db,
        organisation_id=organisation_id,
        query_embedding=query_embedding,
        limit=limit,
    )
    evidence: list[dict[str, Any]] = []

    for chunk in chunks:
        # The vector query is organisation-filtered; retain this second check
        # while creating evidence so malformed provider rows cannot leak data.
        if chunk.get("organisation_id") != organisation_id:
            continue

        chunk_id = chunk["chunk_id"]
        document_id = chunk["document_id"]
        evidence.append({
            "evidence_id": f"document-chunk:{chunk_id}",
            "content": chunk["content"],
            "provenance": {
                "source_type": "internal_document",
                "source_id": f"document:{document_id}",
                "title": chunk["title"],
                "uri": chunk["source_uri"],
                "organisation_id": organisation_id,
                "metadata": {
                    "chunk_id": chunk_id,
                    "chunk_index": chunk["chunk_index"],
                    "content_hash": chunk.get("content_hash"),
                    "chunk_metadata": chunk.get("metadata"),
                    "embedding_dimension": chunk.get("embedding_dimension"),
                },
            },
            "score": chunk.get("similarity"),
            "metadata": {"document_id": document_id},
        })

    return evidence


__all__ = ["search_internal_knowledge"]
