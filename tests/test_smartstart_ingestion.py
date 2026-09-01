from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.smartstart_ingestion_service import (
    SKIP_ENV_VAR,
    ingest_smartstart_website,
    should_skip_live_ingest,
)
from app.services.web_ingestion_service import WebDocument, calculate_content_hash
from app.tools.internal_knowledge_tool import search_internal_knowledge


MODEL_TEXT = (
    "SmartStart's social franchise model enables women to run quality "
    "home and community based early learning programmes. The programme "
    "is supported by licensing and quality assurance processes."
)
QUALITY_TEXT = (
    "Programme quality is maintained by a national team of Coaches "
    "and a quality assurance process for every early learning programme."
)


def _page(url: str, title: str, content: str) -> WebDocument:
    return WebDocument(
        url=url,
        title=title,
        content=content,
        content_hash=calculate_content_hash(content),
    )


def _pages():
    return [
        _page(
            "https://smartstart.org.za/about-us/",
            "About Us | SmartStart",
            MODEL_TEXT,
        ),
        _page(
            "https://smartstart.org.za/impact/",
            "Impact | SmartStart",
            QUALITY_TEXT,
        ),
    ]


def _patch_ingest_stack(monkeypatch, organisation_id=1):
    created = {
        "documents": [],
        "ingested": [],
        "knowledge_sources": [],
    }

    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.get_organisation",
        lambda db, oid: {
            "id": oid,
            "name": "BrightStart ECD Network",
            "country": "South Africa",
        },
    )

    def knowledge_source(**kwargs):
        source = {
            "id": 4,
            "organisation_id": kwargs["organisation_id"],
            "name": kwargs["name"],
            "source_type": kwargs["source_type"],
            "base_url": kwargs["base_url"],
        }
        created["knowledge_sources"].append(source)
        return source

    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.get_or_create_knowledge_source",
        knowledge_source,
    )

    def upsert(**kwargs):
        document = {
            "id": len(created["documents"]) + 1,
            "organisation_id": kwargs["organisation_id"],
            "knowledge_source_id": kwargs["knowledge_source_id"],
            "title": kwargs["title"],
            "document_type": kwargs["document_type"],
            "source_uri": kwargs["source_uri"],
            "content_hash": kwargs["content_hash"],
            "status": "active",
        }
        created["documents"].append(document)
        return document, True

    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.upsert_document",
        upsert,
    )

    def ingest(**kwargs):
        created["ingested"].append(kwargs)
        return {
            "document_id": kwargs["document_id"],
            "chunks_created": 2,
            "embeddings_created": 2,
        }

    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.ingest_document",
        ingest,
    )
    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.crawl_public_pages",
        lambda *args, **kwargs: _pages(),
    )
    return created


def test_should_skip_live_ingest_honours_flag_and_env(monkeypatch):
    monkeypatch.delenv(SKIP_ENV_VAR, raising=False)
    assert should_skip_live_ingest(False) is False
    assert should_skip_live_ingest(True) is True
    monkeypatch.setenv(SKIP_ENV_VAR, "1")
    assert should_skip_live_ingest() is True


def test_ingest_skips_without_crawling(monkeypatch):
    crawl = MagicMock(side_effect=AssertionError("live crawl should not run"))
    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.crawl_public_pages",
        crawl,
    )
    summary = ingest_smartstart_website(
        MagicMock(),
        organisation_id=1,
        skip=True,
    )
    assert summary["skipped"] is True
    assert summary["documents_ingested"] == 0
    crawl.assert_not_called()


def test_ingest_is_offline_safe_when_crawl_fails(monkeypatch):
    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.get_organisation",
        lambda db, oid: {"id": oid, "name": "BrightStart ECD Network", "country": "ZA"},
    )
    monkeypatch.setattr(
        "app.services.smartstart_ingestion_service.crawl_public_pages",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("DNS down")),
    )
    summary = ingest_smartstart_website(
        MagicMock(),
        organisation_id=1,
        offline_safe=True,
    )
    assert summary["skipped"] is True
    assert "live crawl unavailable" in summary["reason"]


def test_ingest_stores_organisation_scoped_smartstart_documents(monkeypatch):
    created = _patch_ingest_stack(monkeypatch)
    summary = ingest_smartstart_website(MagicMock(), organisation_id=1)

    assert summary["skipped"] is False
    assert summary["organisation_id"] == 1
    assert summary["pages_crawled"] == 2
    assert summary["documents_ingested"] == 2
    assert summary["chunks_created"] == 4
    assert created["knowledge_sources"][0]["organisation_id"] == 1
    assert {doc["source_uri"] for doc in created["documents"]} == {
        "https://smartstart.org.za/about-us/",
        "https://smartstart.org.za/impact/",
    }
    assert all(item["organisation_id"] == 1 for item in created["ingested"])
    assert MODEL_TEXT in created["ingested"][0]["content"]


def test_ingest_keeps_tenant_isolation(monkeypatch):
    created = _patch_ingest_stack(monkeypatch)
    ingest_smartstart_website(MagicMock(), organisation_id=7)
    assert created["knowledge_sources"][0]["organisation_id"] == 7
    assert all(doc["organisation_id"] == 7 for doc in created["documents"])
    assert all(item["organisation_id"] == 7 for item in created["ingested"])


def test_retrieval_returns_citations_from_ingested_pages(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
    )
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [
            {
                "chunk_id": 11,
                "document_id": 3,
                "organisation_id": kwargs["organisation_id"],
                "chunk_index": 0,
                "content": MODEL_TEXT,
                "content_hash": "hash",
                "metadata": {"url": "https://smartstart.org.za/about-us/"},
                "embedding_dimension": 3,
                "title": "About Us | SmartStart",
                "source_uri": "https://smartstart.org.za/about-us/",
                "similarity": 0.91,
            }
        ],
    )

    evidence = search_internal_knowledge(
        "What is SmartStart's model?",
        1,
        MagicMock(),
    )

    assert evidence[0]["content"] == MODEL_TEXT
    assert evidence[0]["provenance"]["uri"] == "https://smartstart.org.za/about-us/"
    assert evidence[0]["provenance"]["organisation_id"] == 1
    assert "social franchise model" in evidence[0]["content"]


def test_retrieval_does_not_return_other_organisation_chunks(monkeypatch):
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.embed_text",
        lambda question: SimpleNamespace(embedding=[0.1]),
    )
    monkeypatch.setattr(
        "app.tools.internal_knowledge_tool.search_similar_chunks",
        lambda **kwargs: [
            {
                "chunk_id": 11,
                "document_id": 3,
                "organisation_id": 99,
                "chunk_index": 0,
                "content": MODEL_TEXT,
                "content_hash": "hash",
                "metadata": {},
                "embedding_dimension": 1,
                "title": "About Us | SmartStart",
                "source_uri": "https://smartstart.org.za/about-us/",
                "similarity": 0.91,
            }
        ],
    )
    assert search_internal_knowledge("What is SmartStart's model?", 1, MagicMock()) == []
