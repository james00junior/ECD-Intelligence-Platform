"""
Recommended small Ollama models for local query planning benchmarks.

Ollama tag names can differ from Hugging Face repo names. Use these tags
with ``ollama pull`` and ``OLLAMA_MODEL``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalModelSpec:
    """Metadata for a local Ollama model."""

    ollama_tag: str
    approx_size: str
    description: str
    hf_name: str | None = None


RECOMMENDED_PLANNER_MODELS: tuple[LocalModelSpec, ...] = (
    LocalModelSpec(
        ollama_tag="qwen3.5:0.8b",
        approx_size="~1.0 GB",
        description="Tiny multimodal Qwen; fast on CPU and low-VRAM GPUs.",
        hf_name="Qwen/Qwen3.5-0.8B",
    ),
    LocalModelSpec(
        ollama_tag="gemma4:e2b",
        approx_size="~2 GB",
        description=(
            "Gemma 4 E2B nano instruct model. Closest Ollama match to "
            "gemma3n-e2-it style edge models."
        ),
        hf_name="google/gemma-3n-E2B-it",
    ),
    LocalModelSpec(
        ollama_tag="phi4-mini",
        approx_size="~2.5 GB",
        description="Microsoft Phi-4 mini; strong small-model reasoning.",
        hf_name="microsoft/Phi-4-mini-instruct",
    ),
    LocalModelSpec(
        ollama_tag="gemma3:1b",
        approx_size="~815 MB",
        description="Lightweight Gemma 3 fallback if Gemma 4 nano is too new.",
        hf_name="google/gemma-3-1b-it",
    ),
    LocalModelSpec(
        ollama_tag="qwen2.5:0.5b",
        approx_size="~397 MB",
        description="Smallest practical Qwen; good sanity-check baseline.",
        hf_name="Qwen/Qwen2.5-0.5B-Instruct",
    ),
    LocalModelSpec(
        ollama_tag="llama3.2:1b",
        approx_size="~1.3 GB",
        description="Meta 1B baseline for comparison.",
        hf_name="meta-llama/Llama-3.2-1B-Instruct",
    ),
)


DEFAULT_BENCHMARK_MODELS: tuple[str, ...] = tuple(
    model.ollama_tag for model in RECOMMENDED_PLANNER_MODELS[:3]
)


def model_tags() -> list[str]:
    return [model.ollama_tag for model in RECOMMENDED_PLANNER_MODELS]


__all__ = [
    "DEFAULT_BENCHMARK_MODELS",
    "LocalModelSpec",
    "RECOMMENDED_PLANNER_MODELS",
    "model_tags",
]
