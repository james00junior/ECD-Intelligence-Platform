from __future__ import annotations

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural-language analytics question.",
    )


class AgentResponse(BaseModel):
    error: str | None = None
    intent: str | None = None
    route: str | None = None
    query: str | None = None
    sql_query: str | None = None
    answer: str | None = None
    results: list[dict] = Field(default_factory=list)
