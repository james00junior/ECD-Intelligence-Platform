from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException

from app.api.schemas import AgentRequest
from app.api.schemas import AgentResponse
from app.workflows.analytics_workflow import analytics_workflow


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


@router.post(
    "/query",
    response_model=AgentResponse,
)
def run_agent(
    request: AgentRequest,
) -> AgentResponse:

    try:
        result = analytics_workflow.invoke(
            {
                "question": request.question,
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
        sql_query=result.get("sql_query"),
        results=result.get("results", []),
        sources=[
            "PostgreSQL ECD intelligence database",
        ],
        error=result.get("error"),
    )