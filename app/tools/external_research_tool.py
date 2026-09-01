"""Controlled external research abstraction for the Research Agent."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol, TypedDict
from urllib.parse import urlparse

import requests


class ExternalSearchResult(TypedDict):
    title: str
    url: str
    snippet: str


class ExternalResearchProvider(Protocol):
    """Minimal provider contract, making web research replaceable and mockable."""

    def search(self, question: str, limit: int) -> list[ExternalSearchResult]:
        ...


class DuckDuckGoInstantAnswerProvider:
    """Public web-search provider with bounded timeout and no credentials."""

    endpoint = "https://api.duckduckgo.com/"

    def search(self, question: str, limit: int) -> list[ExternalSearchResult]:
        response = requests.get(
            self.endpoint,
            params={
                "q": question,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        results: list[ExternalSearchResult] = []
        abstract = payload.get("AbstractText")
        abstract_url = payload.get("AbstractURL")
        abstract_title = payload.get("Heading") or "DuckDuckGo result"
        if abstract and abstract_url:
            results.append({
                "title": abstract_title,
                "url": abstract_url,
                "snippet": abstract,
            })
        for topic in payload.get("RelatedTopics", []):
            if len(results) >= limit:
                break
            if not isinstance(topic, dict):
                continue
            text = topic.get("Text")
            url = topic.get("FirstURL")
            if text and url:
                results.append({
                    "title": text.split(" - ", 1)[0],
                    "url": url,
                    "snippet": text,
                })
        return results[:limit]


def _is_safe_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def search_external_research(
    question: str,
    provider: ExternalResearchProvider | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve public evidence without passing organisation data to the web."""

    if not isinstance(question, str) or not question.strip():
        return {"evidence": [], "error": "Question cannot be empty."}
    if limit < 1:
        return {"evidence": [], "error": "limit must be greater than zero."}

    provider = provider or DuckDuckGoInstantAnswerProvider()
    try:
        results = provider.search(question, limit)
    except requests.Timeout:
        return {"evidence": [], "error": "External research timed out."}
    except requests.RequestException as exc:
        return {"evidence": [], "error": f"External research failed: {exc}"}
    except Exception as exc:
        return {"evidence": [], "error": f"External research failed: {exc}"}

    evidence: list[dict[str, Any]] = []
    for result in results:
        title = result.get("title", "").strip()
        url = result.get("url", "").strip()
        snippet = result.get("snippet", "").strip()
        if not title or not snippet or not _is_safe_url(url):
            continue
        source_hash = sha256(url.encode("utf-8")).hexdigest()[:16]
        evidence.append({
            "evidence_id": f"external:{source_hash}",
            "content": snippet,
            "provenance": {
                "source_type": "external",
                "source_id": url,
                "title": title,
                "uri": url,
                "organisation_id": None,
                "metadata": {},
            },
            "score": None,
            "metadata": {"provider": type(provider).__name__},
        })
    return {"evidence": evidence, "error": None}


__all__ = [
    "DuckDuckGoInstantAnswerProvider",
    "ExternalResearchProvider",
    "ExternalSearchResult",
    "search_external_research",
]
