from app.workflows.research_workflow import initial_routing_node, research_workflow


def test_initial_routing_node_preserves_existing_evidence():
    evidence = [
        {
            "evidence_id": "document-chunk-1",
            "content": "Programme quality improves with support.",
            "provenance": {
                "source_type": "internal_document",
                "source_id": "chunk-1",
                "title": "Programme guide",
                "uri": "document://programme-guide",
                "organisation_id": 1,
                "metadata": {},
            },
            "score": 0.91,
            "metadata": {},
        }
    ]

    result = initial_routing_node(
        {
            "question": "What does our programme guide say about quality?",
            "organisation_id": 1,
            "evidence": evidence,
            "research_steps": 1,
        }
    )

    assert result["route"] == "internal_knowledge"
    assert result["evidence"] == evidence
    assert result["research_steps"] == 1
    assert result["error"] is None


def test_research_workflow_terminates_for_direct_question():
    result = research_workflow.invoke(
        {
            "question": "Hello there",
            "organisation_id": 1,
        }
    )

    assert result["route"] == "direct"
    assert result["source_requirements"] == []
    assert result["evidence"] == []
    assert result["research_steps"] == 0
    assert result["answer"] is None
    assert result["error"] == "No research source was selected for this question."


def test_research_workflow_preserves_organisation_scope(monkeypatch):
    monkeypatch.setattr(
        "app.workflows.research_workflow.search_internal_knowledge",
        lambda **kwargs: [],
    )
    result = research_workflow.invoke(
        {
            "question": "Summarise the organisation's programme guide.",
            "organisation_id": 42,
        }
    )

    assert result["organisation_id"] == 42
    assert result["route"] == "internal_knowledge"


def test_research_workflow_collects_sql_and_document_evidence(monkeypatch):
    sql_evidence = {
        "evidence_id": "sql:count_franchisees",
        "content": "[{\"franchisee_count\": 4}]",
        "provenance": {
            "source_type": "sql", "source_id": "sql:count_franchisees",
            "title": "Database", "uri": None, "organisation_id": 1,
            "metadata": {},
        },
        "score": None, "metadata": {},
    }
    document_evidence = {
        "evidence_id": "document-chunk:1",
        "content": "Coaching supports quality.",
        "provenance": {
            "source_type": "internal_document", "source_id": "document:1",
            "title": "Report", "uri": "document://report", "organisation_id": 1,
            "metadata": {},
        },
        "score": 0.9, "metadata": {},
    }

    monkeypatch.setattr(
        "app.workflows.research_workflow.run_sql_research",
        lambda **kwargs: {"evidence": [sql_evidence], "error": None},
    )
    monkeypatch.setattr(
        "app.workflows.research_workflow.search_internal_knowledge",
        lambda **kwargs: [document_evidence],
    )

    result = research_workflow.invoke(
        {
            "question": "How many franchisees are there, and what does our report say?",
            "organisation_id": 1,
        }
    )

    assert result["route"] == "sql_and_internal_knowledge"
    assert result["source_requirements"] == ["sql", "internal_document"]
    assert result["evidence"] == [sql_evidence, document_evidence]
    assert result["research_steps"] == 2


def test_research_workflow_collects_external_evidence(monkeypatch):
    external_evidence = {
        "evidence_id": "external:1",
        "content": "Public ECD research supports coaching.",
        "provenance": {
            "source_type": "external",
            "source_id": "https://example.com/research",
            "title": "ECD research",
            "uri": "https://example.com/research",
            "organisation_id": None,
            "metadata": {},
        },
        "score": None,
        "metadata": {},
    }
    monkeypatch.setattr(
        "app.workflows.research_workflow.search_external_research",
        lambda question: {"evidence": [external_evidence], "error": None},
    )

    result = research_workflow.invoke(
        {"question": "Find public research on ECD quality.", "organisation_id": 1}
    )

    assert result["route"] == "external"
    assert result["selected_evidence"] == [external_evidence]
    assert result["citations"][0]["source_kind"] == "external"


def test_research_workflow_retries_with_refined_query(monkeypatch):
    calls = []
    evidence = {
        "evidence_id": "document-chunk:1",
        "content": "Coaching improves quality.",
        "provenance": {
            "source_type": "internal_document",
            "source_id": "document:1",
            "title": "Programme guide",
            "uri": "document://guide",
            "organisation_id": 1,
            "metadata": {},
        },
        "score": 0.9,
        "metadata": {},
    }

    def retrieve(**kwargs):
        calls.append(kwargs["question"])
        return [] if len(calls) == 1 else [evidence]

    monkeypatch.setattr(
        "app.workflows.research_workflow.search_internal_knowledge", retrieve
    )
    result = research_workflow.invoke({
        "question": "What does our programme guide say?",
        "organisation_id": 1,
        "max_research_steps": 2,
    })

    assert len(calls) == 2
    assert calls[1].endswith("supporting evidence.")
    assert result["research_attempts"] == 1
    assert result["research_steps"] == 2
    assert result["answer"] is not None
