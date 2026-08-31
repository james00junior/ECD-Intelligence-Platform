from typing import Any

from pydantic import BaseModel


class AgentRequest(BaseModel):
    question: str


class AgentResponse(BaseModel):
    answer: str
    intent: str | None = None
    sql_query: str | None = None
    results: list[dict[str, Any]]
    sources: list[str]