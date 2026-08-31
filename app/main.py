from __future__ import annotations

from fastapi import FastAPI

from app.api.schemas import AgentRequest, AgentResponse
from app.workflows.analytics_workflow import analytics_workflow


app = FastAPI(
    title="ECD Intelligence Platform",
    description="Enterprise analytics agent platform.",
    version="0.1.0",
)



@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok"
    }



@app.post(
    "/agent",
    response_model=AgentResponse,
)
def agent(request: AgentRequest) -> dict:
    result = analytics_workflow.invoke(
        {
            "question": request.question,
        }
    )

    return result






