from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_knowledge_source(
    db: Session,
    organisation_id: int,
    name: str,
    source_type: str,
    base_url: str | None = None,
) -> dict:
    query = text(
        """
        INSERT INTO knowledge_sources (
            organisation_id,
            name,
            source_type,
            base_url
        )
        VALUES (
            :organisation_id,
            :name,
            :source_type,
            :base_url
        )
        RETURNING
            id,
            organisation_id,
            name,
            source_type,
            base_url
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "name": name,
            "source_type": source_type,
            "base_url": base_url,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise RuntimeError(
            "Knowledge source could not be created."
        )

    return dict(row)


def get_knowledge_source_by_name(
    db: Session,
    organisation_id: int,
    name: str,
) -> dict | None:
    query = text(
        """
        SELECT
            id,
            organisation_id,
            name,
            source_type,
            base_url
        FROM knowledge_sources
        WHERE organisation_id = :organisation_id
          AND name = :name
        ORDER BY id
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "name": name,
        },
    ).mappings().first()

    return dict(row) if row is not None else None


def get_or_create_knowledge_source(
    db: Session,
    organisation_id: int,
    name: str,
    source_type: str,
    base_url: str | None = None,
) -> dict:
    existing = get_knowledge_source_by_name(
        db=db,
        organisation_id=organisation_id,
        name=name,
    )
    if existing is not None:
        return existing

    return create_knowledge_source(
        db=db,
        organisation_id=organisation_id,
        name=name,
        source_type=source_type,
        base_url=base_url,
    )


def create_document(
    db: Session,
    organisation_id: int,
    knowledge_source_id: int,
    title: str,
    document_type: str,
    source_uri: str,
    content_hash: str | None = None,
    status: str = "active",
) -> dict:
    query = text(
        """
        INSERT INTO documents (
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        )
        VALUES (
            :organisation_id,
            :knowledge_source_id,
            :title,
            :document_type,
            :source_uri,
            :content_hash,
            :status
        )
        RETURNING
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "knowledge_source_id": knowledge_source_id,
            "title": title,
            "document_type": document_type,
            "source_uri": source_uri,
            "content_hash": content_hash,
            "status": status,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise RuntimeError(
            "Document could not be created."
        )

    return dict(row)


def get_document_by_source_uri(
    db: Session,
    organisation_id: int,
    source_uri: str,
) -> dict | None:
    query = text(
        """
        SELECT
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        FROM documents
        WHERE organisation_id = :organisation_id
          AND source_uri = :source_uri
        ORDER BY id
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "source_uri": source_uri,
        },
    ).mappings().first()

    return dict(row) if row is not None else None


def update_document(
    db: Session,
    organisation_id: int,
    document_id: int,
    title: str,
    content_hash: str | None,
    status: str = "active",
) -> dict:
    query = text(
        """
        UPDATE documents
        SET
            title = :title,
            content_hash = :content_hash,
            status = :status
        WHERE id = :document_id
          AND organisation_id = :organisation_id
        RETURNING
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        """
    )

    row = db.execute(
        query,
        {
            "organisation_id": organisation_id,
            "document_id": document_id,
            "title": title,
            "content_hash": content_hash,
            "status": status,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise ValueError(
            "Document does not exist for this organisation."
        )

    return dict(row)


def upsert_document(
    db: Session,
    organisation_id: int,
    knowledge_source_id: int,
    title: str,
    document_type: str,
    source_uri: str,
    content_hash: str | None = None,
    status: str = "active",
) -> tuple[dict, bool]:
    """Create or update a document for one organisation.

    Returns the document row and whether the content should be re-chunked.
    """

    existing = get_document_by_source_uri(
        db=db,
        organisation_id=organisation_id,
        source_uri=source_uri,
    )

    if existing is None:
        created = create_document(
            db=db,
            organisation_id=organisation_id,
            knowledge_source_id=knowledge_source_id,
            title=title,
            document_type=document_type,
            source_uri=source_uri,
            content_hash=content_hash,
            status=status,
        )
        return created, True

    if (
        existing.get("content_hash") == content_hash
        and existing.get("title") == title
        and existing.get("status") == status
    ):
        return existing, False

    updated = update_document(
        db=db,
        organisation_id=organisation_id,
        document_id=existing["id"],
        title=title,
        content_hash=content_hash,
        status=status,
    )
    content_changed = existing.get("content_hash") != content_hash
    return updated, content_changed


def list_documents(
    db: Session,
    organisation_id: int,
) -> list[dict]:
    query = text(
        """
        SELECT
            id,
            organisation_id,
            knowledge_source_id,
            title,
            document_type,
            source_uri,
            content_hash,
            status
        FROM documents
        WHERE organisation_id = :organisation_id
        ORDER BY id
        """
    )

    rows = db.execute(
        query,
        {
            "organisation_id": organisation_id,
        },
    ).mappings().all()

    return [dict(row) for row in rows]
