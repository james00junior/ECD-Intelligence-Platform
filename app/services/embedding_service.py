from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import requests
from sentence_transformers import SentenceTransformer


DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
FALLBACK_PROVIDER = "sentence-transformers"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

EmbeddingProvider = Literal[
    "ollama",
    "sentence-transformers",
    "sentence_transformer",
]


@dataclass(frozen=True)
class EmbeddingResult:
    """
    Embedding together with the information required to
    reproduce and interpret it.
    """

    embedding: list[float]
    provider: str
    model: str
    dimension: int


def _validate_text(text: str) -> None:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")


def _validate_texts(texts: list[str]) -> None:
    if any(not text or not text.strip() for text in texts):
        raise ValueError("Documents cannot contain empty text.")


@lru_cache(maxsize=4)
def get_embedding_model(
    model_name: str,
) -> SentenceTransformer:
    """
    Load and cache a Sentence Transformers model.
    """

    return SentenceTransformer(model_name)


def _embed_ollama(
    texts: list[str],
    model_name: str,
    base_url: str,
) -> list[list[float]]:
    """
    Generate embeddings using Ollama.
    """

    response = requests.post(
        f"{base_url.rstrip('/')}/api/embed",
        json={
            "model": model_name,
            "input": texts,
        },
        timeout=120,
    )

    response.raise_for_status()

    payload = response.json()

    embeddings = payload.get("embeddings")

    if not embeddings:
        raise ValueError(
            "Ollama returned no embeddings."
        )

    return embeddings


def _embed_sentence_transformers(
    texts: list[str],
    model_name: str,
) -> list[list[float]]:
    """
    Generate embeddings using Sentence Transformers.
    """

    model = get_embedding_model(model_name)

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


def embed_documents(
    texts: list[str],
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> list[EmbeddingResult]:
    """
    Generate embeddings using the configured provider.

    The dimensionality is discovered from the returned
    embedding vector rather than being hard-coded.
    """

    if not texts:
        return []

    _validate_texts(texts)

    provider = provider.lower().strip()

    if provider == "ollama":
        embeddings = _embed_ollama(
            texts=texts,
            model_name=model_name,
            base_url=ollama_base_url,
        )

    elif provider in {
        "sentence-transformers",
        "sentence_transformer",
    }:
        embeddings = _embed_sentence_transformers(
            texts=texts,
            model_name=model_name,
        )

    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider}"
        )

    if not embeddings:
        return []

    dimension = len(embeddings[0])

    if any(len(vector) != dimension for vector in embeddings):
        raise ValueError(
            "Embedding provider returned vectors with "
            "inconsistent dimensions."
        )

    return [
        EmbeddingResult(
            embedding=vector,
            provider=provider,
            model=model_name,
            dimension=dimension,
        )
        for vector in embeddings
    ]


def embed_documents_with_fallback(
    texts: list[str],
    provider: str | None = None,
    model_name: str | None = None,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> list[EmbeddingResult]:
    """
    Generate embeddings, falling back from Ollama to
    Sentence Transformers when the preferred provider fails.
    """

    preferred_provider = (provider or DEFAULT_PROVIDER).lower().strip()
    preferred_model = model_name or DEFAULT_MODEL

    try:
        return embed_documents(
            texts,
            provider=preferred_provider,
            model_name=preferred_model,
            ollama_base_url=ollama_base_url,
        )
    except Exception:
        if preferred_provider in {
            "sentence-transformers",
            "sentence_transformer",
        }:
            raise
        return embed_documents(
            texts,
            provider=FALLBACK_PROVIDER,
            model_name=FALLBACK_MODEL,
            ollama_base_url=ollama_base_url,
        )


def embed_text(
    text: str,
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> EmbeddingResult:
    """
    Generate an embedding for a single text.
    """

    _validate_text(text)

    results = embed_documents(
        [text],
        provider=provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
    )

    return results[0]


def embedding_dimension(
    provider: str = DEFAULT_PROVIDER,
    model_name: str = DEFAULT_MODEL,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> int:
    """
    Discover the embedding dimension from the actual model output.

    No embedding dimension is hard-coded.
    """

    result = embed_text(
        "dimension discovery test",
        provider=provider,
        model_name=model_name,
        ollama_base_url=ollama_base_url,
    )

    return result.dimension
