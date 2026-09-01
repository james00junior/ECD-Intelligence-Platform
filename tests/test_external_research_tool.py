import requests

from app.tools.external_research_tool import search_external_research


class FakeProvider:
    def search(self, question, limit):
        assert "ECD" in question
        assert limit == 5
        return [{
            "title": "ECD evidence",
            "url": "https://example.com/evidence",
            "snippet": "Coaching supports programme quality.",
        }]


def test_returns_external_evidence_without_organisation_identity():
    result = search_external_research("Find ECD evidence", provider=FakeProvider())

    evidence = result["evidence"][0]
    assert result["error"] is None
    assert evidence["provenance"]["organisation_id"] is None
    assert evidence["provenance"]["uri"] == "https://example.com/evidence"
    assert evidence["provenance"]["title"] == "ECD evidence"


def test_rejects_unsafe_provider_url():
    class UnsafeProvider:
        def search(self, question, limit):
            return [{"title": "Unsafe", "url": "file:///secret", "snippet": "No"}]

    result = search_external_research("Find ECD evidence", provider=UnsafeProvider())
    assert result == {"evidence": [], "error": None}


def test_handles_provider_timeout():
    class TimeoutProvider:
        def search(self, question, limit):
            raise requests.Timeout()

    result = search_external_research("Find ECD evidence", provider=TimeoutProvider())
    assert result["evidence"] == []
    assert result["error"] == "External research timed out."
