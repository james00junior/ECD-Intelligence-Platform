from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import text

from app.api.schemas import AgentRequest
from app.api.schemas import AgentResponse
from app.database.database import engine
from app.workflows.analytics_workflow import analytics_workflow


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


def organisation_exists(organisation_id: int) -> bool:
    """
    Check whether an organisation exists.

    This validation happens before the analytics workflow so that
    a nonexistent organisation is distinguishable from an existing
    organisation that simply has zero matching records.
    """

    query = text(
        """
        SELECT 1
        FROM organisations
        WHERE id = :organisation_id
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {
                "organisation_id": organisation_id,
            },
        )

        return result.first() is not None


@router.post(
    "/query",
    response_model=AgentResponse,
)
def run_agent(
    request: AgentRequest,
) -> AgentResponse:

    # ---------------------------------------------------------------
    # Organisation validation
    # ---------------------------------------------------------------

    if request.organisation_id is not None:

        if not organisation_exists(
            request.organisation_id
        ):
            return AgentResponse(
                answer=None,
                intent=None,
                route="analytics",
                query=None,
                sql_query=None,
                results=[],
                sources=[
                    "PostgreSQL ECD intelligence database",
                ],
                error=(
                    f"Organisation "
                    f"{request.organisation_id} "
                    f"does not exist."
                ),
            )

    # ---------------------------------------------------------------
    # Analytics workflow
    # ---------------------------------------------------------------

    try:
        result = analytics_workflow.invoke(
            {
                "question": request.question,
                "organisation_id": request.organisation_id,
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {exc}",
        ) from exc

    return AgentResponse(
        answer=result.get("answer"),
        intent=result.get("intent"),
        route=result.get("route"),
        query=result.get("query"),
        sql_query=result.get("sql_query"),
        results=result.get("results", []),
        sources=[
            "PostgreSQL ECD intelligence database",
        ],
        error=result.get("error"),
        sql_source=result.get("sql_source"),
        planner_latency_ms=result.get("planner_latency_ms"),
        fallback_used=result.get("fallback_used"),
    )