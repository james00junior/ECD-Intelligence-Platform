from fastapi import FastAPI

from app.api.schemas import AgentRequest
from app.api.schemas import AgentResponse
from app.api.v1.router import router as api_router
from app.workflows.analytics_workflow import analytics_workflow


app = FastAPI(
    title="ECD Intelligence Platform",
    description=(
        "Enterprise AI intelligence platform for "
        "data analytics, organisational knowledge, "
        "and decision support."
    ),
    version="0.3.0",
)


# -------------------------------------------------------------------
# Versioned API
# -------------------------------------------------------------------

app.include_router(
    api_router,
)


# -------------------------------------------------------------------
# Legacy API
#
# Kept for backwards compatibility with existing clients/tests.
# -------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.post(
    "/agent",
    response_model=AgentResponse,
)
def agent(
    request: AgentRequest,
) -> AgentResponse:

    result = analytics_workflow.invoke(
        {
            "question": request.question,
        }
    )

    return AgentResponse(
        answer=result.get("answer"),
        intent=result.get("intent"),
        route=result.get("route"),
        query=result.get("sql_query"),
        sql_query=result.get("sql_query"),
        results=result.get("results", []),
        sources=[
            "PostgreSQL ECD intelligence database",
        ],
        error=result.get("error"),
    )