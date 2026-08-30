from fastapi import FastAPI
from fastapi import HTTPException

from app.agents.analytics_agent import analytics_agent
from app.schemas.agent import AgentRequest
from app.schemas.agent import AgentResponse


app = FastAPI(
    title="Enterprise Agent Platform",
    description="Multi-agent AI platform for enterprise data analysis.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """
    Basic health check.
    """

    return {
        "status": "ok",
    }


@app.post(
    "/agent",
    response_model=AgentResponse,
)
def run_agent(
    request: AgentRequest,
) -> AgentResponse:
    """
    Run the Analytics Agent against a natural-language question.
    """

    initial_state = {
        "question": request.question,
        "sql_query": None,
        "results": [],
        "answer": None,
        "error": None,
    }

    try:

        result = analytics_agent.invoke(
            initial_state
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {exc}",
        )

    return AgentResponse(
        answer=result["answer"] or "",
        sql_query=result["sql_query"],
        results=result["results"],
        sources=[
            "PostgreSQL survey database"
        ],
    )
