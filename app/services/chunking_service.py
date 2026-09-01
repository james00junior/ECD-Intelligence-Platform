from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class DocumentChunk:
    """
    A deterministic chunk of a source document.
    """

    chunk_index: int
    content: str


def normalise_text(text: str) -> str:
    """
    Normalise whitespace while preserving paragraph boundaries.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    paragraphs = re.split(r"\n\s*\n+", text)

    cleaned_paragraphs: list[str] = []

    for paragraph in paragraphs:
        paragraph = re.sub(r"[ \t]+", " ", paragraph)
        paragraph = re.sub(r"\n+", " ", paragraph)
        paragraph = paragraph.strip()

        if paragraph:
            cleaned_paragraphs.append(paragraph)

    return "\n\n".join(cleaned_paragraphs)


def chunk_document(
    content: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[DocumentChunk]:
    """
    Split document text into deterministic overlapping chunks.

    Parameters
    ----------
    content:
        Source document text.

    chunk_size:
        Maximum number of characters per chunk.

    chunk_overlap:
        Number of characters shared between neighbouring chunks.

    Returns
    -------
    list[DocumentChunk]
        Ordered document chunks.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    content = normalise_text(content)

    if not content:
        return []

    chunks: list[DocumentChunk] = []

    start = 0
    chunk_index = 0

    while start < len(content):
        end = min(
            start + chunk_size,
            len(content),
        )

        chunk_text = content[start:end].strip()

        if chunk_text:
            chunks.append(
                DocumentChunk(
                    chunk_index=chunk_index,
                    content=chunk_text,
                )
            )

            chunk_index += 1

        if end >= len(content):
            break

        start = end - chunk_overlap

    return chunks
