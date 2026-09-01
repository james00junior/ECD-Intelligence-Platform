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


class HealthResponse(BaseModel):
    status: str

    version: str


class OrganisationResponse(BaseModel):
    id: int

    name: str

    country: str