"""Local model catalog and planner-mode inspection (test-oriented)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config.local_models import RECOMMENDED_PLANNER_MODELS
from app.config.settings import get_settings
from app.services import ollama_client


router = APIRouter(prefix="/models", tags=["models"])


class PlannerStatus(BaseModel):
    query_planner_mode: str
    llm_provider: str
    ollama_model: str
    ollama_base_url: str
    ollama_reachable: bool


class PullRequest(BaseModel):
    tag: str = Field(..., min_length=1, max_length=120)


@router.get("")
def list_models() -> dict[str, Any]:
    settings = get_settings()
    reachable = ollama_client.ollama_reachable()
    installed: list[dict[str, Any]] = []
    if reachable:
        installed = ollama_client.installed_model_details()

    recommended = [
        {
            "ollama_tag": spec.ollama_tag,
            "approx_size": spec.approx_size,
            "description": spec.description,
            "hf_name": spec.hf_name,
            "installed": (
                ollama_client.model_installed(
                    spec.ollama_tag,
                    {item.get("name", "") for item in installed},
                )
                if reachable
                else False
            ),
        }
        for spec in RECOMMENDED_PLANNER_MODELS
    ]

    return {
        "query_planner_mode": settings.query_planner_mode,
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_reachable": reachable,
        "recommended": recommended,
        "installed": [
            {
                "name": item.get("name"),
                "size": item.get("size"),
                "parameter_size": (item.get("details") or {}).get("parameter_size"),
            }
            for item in installed
        ],
    }


@router.get("/status", response_model=PlannerStatus)
def planner_status() -> PlannerStatus:
    settings = get_settings()
    return PlannerStatus(
        query_planner_mode=settings.query_planner_mode,
        llm_provider=settings.llm_provider,
        ollama_model=settings.ollama_model,
        ollama_base_url=settings.ollama_base_url,
        ollama_reachable=ollama_client.ollama_reachable(),
    )


@router.post("/pull")
def pull_model(request: PullRequest) -> dict[str, Any]:
    """Pull a catalog model. Intended for local testing, not production."""

    allowed = {spec.ollama_tag for spec in RECOMMENDED_PLANNER_MODELS}
    if request.tag not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only recommended planner models can be pulled via the API. "
                f"Allowed: {', '.join(sorted(allowed))}"
            ),
        )
    if not ollama_client.ollama_reachable():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not reachable. Start it, then retry.",
        )
    try:
        ollama_client.pull_model(request.tag)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama pull failed: {exc}",
        ) from exc
    return {"tag": request.tag, "status": "ready"}
