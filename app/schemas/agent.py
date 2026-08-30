from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural-language question from the user.",
    )


class AgentResponse(BaseModel):
    answer: str
    sql_query: str | None = None
    results: list[dict[str, Any]] = []
    sources: list[str] = []
