from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language analytics question.",
    )

    organisation_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional organisation scope.",
    )


class AgentResponse(BaseModel):
    answer: str | None = None

    intent: str | None = None

    route: str | None = None

    query: str | None = None

    sql_query: str | None = None

    results: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    sources: list[str] = Field(
        default_factory=list,
    )

    error: str | None = None

    sql_source: str | None = None

    planner_latency_ms: float | None = None

    fallback_used: bool | None = None


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    organisation_id: int = Field(..., ge=1)
    max_research_steps: int = Field(default=6, ge=1, le=12)


class ResearchResponse(BaseModel):
    answer: str | None = None
    route: str | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    research_steps: int = 0
    research_attempts: int = 0
    error: str | None = None


class HealthResponse(BaseModel):
    status: str

    version: str


class OrganisationResponse(BaseModel):
    id: int

    name: str

    country: str
