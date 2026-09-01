"""Safe, organisation-scoped SQL evidence collection for Research Agent."""

from __future__ import annotations

import json
from typing import Any

from app.agents.analytics_agent import analytics_agent
from app.database.database import SessionLocal
from app.services.organisation_service import organisation_exists
from app.services.query_planner import create_query_plan


def run_sql_research(question: str, organisation_id: int | None) -> dict[str, Any]:
    """Return structured SQL evidence through the existing safety boundary."""

    if not isinstance(question, str) or not question.strip():
        return {"evidence": [], "error": "Question cannot be empty."}
    if not isinstance(organisation_id, int) or organisation_id < 1:
        return {
            "evidence": [],
            "error": "A valid organisation scope is required for SQL research.",
        }

    db = SessionLocal()
    try:
        if not organisation_exists(db, organisation_id):
            return {
                "evidence": [],
                "error": f"Organisation {organisation_id} does not exist.",
            }
    finally:
        db.close()

    plan = create_query_plan(question)
    if plan is None:
        return {
            "evidence": [],
            "error": "No safe SQL query could be generated for this question.",
        }

    result = analytics_agent.invoke({
        "question": question,
        "intent": plan.intent,
        "organisation_id": organisation_id,
    })
    if result.get("error"):
        return {"evidence": [], "error": str(result["error"])}

    rows = result.get("results", [])
    query = result.get("sql_query") or result.get("query")
    return {
        "evidence": [{
            "evidence_id": f"sql:{plan.intent}",
            "content": json.dumps(rows, default=str, sort_keys=True),
            "provenance": {
                "source_type": "sql",
                "source_id": f"analytics-intent:{plan.intent}",
                "title": "PostgreSQL ECD intelligence database",
                "uri": None,
                "organisation_id": organisation_id,
                "metadata": {
                    "intent": plan.intent,
                    "query": query,
                    "parameters": {"organisation_id": organisation_id},
                    "row_count": len(rows),
                },
            },
            "score": None,
            "metadata": {"intent": plan.intent, "query": query},
        }],
        "error": None,
    }


__all__ = ["run_sql_research"]
