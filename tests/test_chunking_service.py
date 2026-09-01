from app.services.chunking_service import (
    chunk_document,
    normalise_text,
)


def test_normalise_text_collapses_whitespace():
    content = """
    Hello     world.


    This   is another paragraph.
    """

    result = normalise_text(content)

    assert result == (
        "Hello world.\n\n"
        "This is another paragraph."
    )


def test_empty_document_returns_no_chunks():
    assert chunk_document("") == []


def test_whitespace_document_returns_no_chunks():
    assert chunk_document("   \n\n   ") == []


def test_document_is_split_into_chunks():
    content = "A" * 2500

    chunks = chunk_document(
        content,
        chunk_size=1000,
        chunk_overlap=100,
    )

    assert len(chunks) == 3


def test_chunk_indexes_are_sequential():
    content = "A" * 2500

    chunks = chunk_document(
        content,
        chunk_size=1000,
        chunk_overlap=100,
    )

    assert [chunk.chunk_index for chunk in chunks] == [
        0,
        1,
        2,
    ]


def test_chunks_respect_chunk_size():
    content = "A" * 2500

    chunks = chunk_document(
        content,
        chunk_size=1000,
        chunk_overlap=100,
    )

    for chunk in chunks:
        assert len(chunk.content) <= 1000


def test_overlap_is_preserved():
    content = "A" * 2500

    chunks = chunk_document(
        content,
        chunk_size=1000,
        chunk_overlap=100,
    )

    assert chunks[0].content[-100:] == chunks[1].content[:100]
    assert chunks[1].content[-100:] == chunks[2].content[:100]


def test_invalid_chunk_size_is_rejected():
    try:
        chunk_document(
            "hello",
            chunk_size=0,
        )
    except ValueError as exc:
        assert "chunk_size" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_invalid_overlap_is_rejected():
    try:
        chunk_document(
            "hello",
            chunk_size=100,
            chunk_overlap=100,
        )
    except ValueError as exc:
        assert "chunk_overlap" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
