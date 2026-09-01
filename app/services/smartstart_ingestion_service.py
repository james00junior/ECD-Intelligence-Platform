"""Ingest the public SmartStart marketing site into an organisation KB."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.services.knowledge_service import (
    get_or_create_knowledge_source,
    upsert_document,
)
from app.services.organisation_service import get_organisation
from app.services.rag_ingestion_service import ingest_document
from app.services.web_ingestion_service import (
    DEFAULT_MAX_PAGES,
    DEFAULT_TIMEOUT,
    FetchHtml,
    WebDocument,
    crawl_public_pages,
)


SMARTSTART_BASE_URL = "https://smartstart.org.za/"
SMARTSTART_KNOWLEDGE_SOURCE_NAME = "SmartStart public website"
SMARTSTART_KNOWLEDGE_SOURCE_TYPE = "web"
SMARTSTART_DOCUMENT_TYPE = "web_page"
SKIP_ENV_VAR = "SMARTSTART_INGEST_SKIP"

SMARTSTART_SEED_URLS: tuple[str, ...] = (
    "https://smartstart.org.za/",
    "https://smartstart.org.za/about-us/",
    "https://smartstart.org.za/programme/",
    "https://smartstart.org.za/our-programme/",
    "https://smartstart.org.za/model/",
    "https://smartstart.org.za/our-model/",
    "https://smartstart.org.za/impact/",
    "https://smartstart.org.za/our-impact/",
    "https://smartstart.org.za/news-media/",
    "https://smartstart.org.za/news/",
    "https://smartstart.org.za/contact/",
    "https://smartstart.org.za/contact-us/",
)


def should_skip_live_ingest(skip: bool | None = None) -> bool:
    """Return True when live crawl is explicitly disabled."""

    if skip is True:
        return True
    value = os.environ.get(SKIP_ENV_VAR, "").strip().lower()
    return value in {"1", "true", "yes", "skip"}


def _empty_summary(
    *,
    skipped: bool,
    reason: str,
    organisation_id: int | None = None,
) -> dict[str, Any]:
    return {
        "skipped": skipped,
        "reason": reason,
        "organisation_id": organisation_id,
        "knowledge_source_id": None,
        "pages_crawled": 0,
        "documents_ingested": 0,
        "documents_unchanged": 0,
        "chunks_created": 0,
        "failures": [],
    }


def ingest_smartstart_website(
    db: Session,
    organisation_id: int,
    *,
    skip: bool | None = None,
    offline_safe: bool = True,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout: int = DEFAULT_TIMEOUT,
    seed_urls: Sequence[str] = SMARTSTART_SEED_URLS,
    fetch_html: FetchHtml | None = None,
    crawl_pages: Callable[..., list[WebDocument]] | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> dict[str, Any]:
    """
    Crawl public SmartStart pages and store organisation-scoped chunks.

    The live network crawl is skipped when ``skip`` is true or
    ``SMARTSTART_INGEST_SKIP`` is set. Network failures are swallowed
    when ``offline_safe`` is true so seed/dev setup can run offline.
    """

    if should_skip_live_ingest(skip):
        return _empty_summary(
            skipped=True,
            reason="SmartStart ingest skipped.",
            organisation_id=organisation_id,
        )

    organisation = get_organisation(db, organisation_id)
    if organisation is None:
        raise ValueError(
            f"Organisation {organisation_id} does not exist."
        )

    crawler = crawl_pages or crawl_public_pages

    try:
        pages = crawler(
            seed_urls,
            max_pages=max_pages,
            timeout=timeout,
            fetch_html=fetch_html,
        )
    except TypeError:
        try:
            pages = crawler(seed_urls)
        except Exception as exc:
            if offline_safe:
                return _empty_summary(
                    skipped=True,
                    reason=f"live crawl unavailable: {exc}",
                    organisation_id=organisation_id,
                )
            raise
    except Exception as exc:
        if offline_safe:
            return _empty_summary(
                skipped=True,
                reason=f"live crawl unavailable: {exc}",
                organisation_id=organisation_id,
            )
        raise

    knowledge_source = get_or_create_knowledge_source(
        db=db,
        organisation_id=organisation_id,
        name=SMARTSTART_KNOWLEDGE_SOURCE_NAME,
        source_type=SMARTSTART_KNOWLEDGE_SOURCE_TYPE,
        base_url=SMARTSTART_BASE_URL,
    )

    documents_ingested = 0
    documents_unchanged = 0
    chunks_created = 0
    failures: list[dict[str, str]] = []

    for page in pages:
        try:
            document, should_embed = upsert_document(
                db=db,
                organisation_id=organisation_id,
                knowledge_source_id=knowledge_source["id"],
                title=page.title,
                document_type=SMARTSTART_DOCUMENT_TYPE,
                source_uri=page.url,
                content_hash=page.content_hash,
            )
            if not should_embed:
                documents_unchanged += 1
                continue

            result = ingest_document(
                db=db,
                organisation_id=organisation_id,
                document_id=document["id"],
                content=page.content,
                metadata={
                    "url": page.url,
                    "title": page.title,
                    "source": "smartstart.org.za",
                },
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
            )
            documents_ingested += 1
            chunks_created += int(result.get("chunks_created", 0))
        except Exception as exc:
            failures.append(
                {
                    "url": page.url,
                    "error": str(exc),
                }
            )

    return {
        "skipped": False,
        "reason": None,
        "organisation_id": organisation_id,
        "knowledge_source_id": knowledge_source["id"],
        "pages_crawled": len(pages),
        "documents_ingested": documents_ingested,
        "documents_unchanged": documents_unchanged,
        "chunks_created": chunks_created,
        "failures": failures,
    }


def ingest_smartstart_for_dev_setup(
    organisation_id: int,
    *,
    skip: bool | None = None,
) -> dict[str, Any]:
    """Run ingest with a short-lived session for seed/dev setup."""

    db = SessionLocal()
    try:
        return ingest_smartstart_website(
            db,
            organisation_id,
            skip=skip,
            offline_safe=True,
        )
    finally:
        db.close()


__all__ = [
    "SKIP_ENV_VAR",
    "SMARTSTART_SEED_URLS",
    "ingest_smartstart_for_dev_setup",
    "ingest_smartstart_website",
    "should_skip_live_ingest",
]
