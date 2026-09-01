from app.services.research_router import (
    route_research_question,
    source_requirements_for_route,
)


def test_routes_analytics_question_to_sql():
    assert route_research_question("How many franchisees are there?") == "sql"


def test_routes_document_question_to_internal_knowledge():
    assert route_research_question("What does our programme guide say?") == "internal_knowledge"


def test_routes_combined_question_to_sql_and_internal_knowledge():
    question = "How many franchisees are there, and what does our report say?"
    assert route_research_question(question) == "sql_and_internal_knowledge"


def test_routes_external_question_without_executing_external_research():
    assert route_research_question("Find public research on ECD quality.") == "external"


def test_routes_non_research_question_directly():
    assert route_research_question("Hello there") == "direct"


def test_routes_empty_question_directly():
    assert route_research_question("") == "direct"


def test_source_requirements_match_route():
    assert source_requirements_for_route("sql_and_internal_knowledge") == [
        "sql",
        "internal_document",
    ]
