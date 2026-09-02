from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Environment variables:
        QUERY_PLANNER_MODE: ``rule`` (default) or ``llm``
        LLM_PROVIDER: ``ollama`` (default) or ``openai``
        OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
        OLLAMA_MODEL: local model tag (default: qwen3.5:0.8b)

        Small-model examples (set OLLAMA_MODEL to any of these):
            qwen3.5:0.8b
            qwen2.5:0.5b
            llama3.2:1b
            gemma3:1b

        Compare models locally and write the Phase 5 report:
            uv run python scripts/compare_planner_models.py --pull --details --write docs/phase5-model-benchmark.md
        OPENAI_API_KEY: required only when LLM_PROVIDER=openai
        OPENAI_MODEL: OpenAI chat model name (default: gpt-4o-mini)
        LLM_SQL_MAX_REPAIRS: bounded text-to-SQL repair attempts (default: 2)
    """

    query_planner_mode: Literal["rule", "llm"] = "rule"
    llm_provider: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:0.8b"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_sql_max_repairs: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
