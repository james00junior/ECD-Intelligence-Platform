"""Versioned Research Agent API."""

from fastapi import APIRouter, HTTPException

from app.api.schemas import ResearchRequest, ResearchResponse
from app.database.database import SessionLocal
from app.services.organisation_service import organisation_exists
from app.workflows.research_workflow import research_workflow


router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchResponse)
def run_research(request: ResearchRequest) -> ResearchResponse:
    """Run tenant-scoped research and return only selected evidence."""

    db = SessionLocal()
    try:
        if not organisation_exists(db, request.organisation_id):
            return ResearchResponse(
                error=f"Organisation {request.organisation_id} does not exist."
            )
    finally:
        db.close()

    try:
        result = research_workflow.invoke({
            "question": request.question,
            "organisation_id": request.organisation_id,
            "max_research_steps": request.max_research_steps,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Research execution failed.") from exc

    return ResearchResponse(
        answer=result.get("answer"),
        route=result.get("route"),
        evidence=result.get("selected_evidence", []),
        citations=result.get("citations", []),
        conflicts=result.get("conflicts", []),
        research_steps=result.get("research_steps", 0),
        research_attempts=result.get("research_attempts", 0),
        error=result.get("error"),
    )
