from app.services.web_ingestion_service import (
    calculate_content_hash,
    extract_document,
    normalise_text,
)


def test_normalise_text_collapses_whitespace():
    text = """
        Hello       world.

        This is
        a test.
    """

    result = normalise_text(text)

    assert result == "Hello world. This is a test."


def test_calculate_content_hash_is_deterministic():
    content = "ECD intelligence platform"

    first = calculate_content_hash(content)
    second = calculate_content_hash(content)

    assert first == second
    assert len(first) == 64


def test_extract_document_removes_non_content_elements():
    html = """
    <html>
        <head>
            <title>ECD Organisation</title>
            <script>
                console.log("remove me");
            </script>
            <style>
                body { color: red; }
            </style>
        </head>

        <body>
            <nav>
                Navigation
            </nav>

            <main>
                <h1>ECD Organisation</h1>
                <p>
                    We support early childhood development.
                </p>
            </main>

            <footer>
                Footer
            </footer>
        </body>
    </html>
    """

    document = extract_document(
        html=html,
        url="https://example.org/about",
    )

    assert document.url == "https://example.org/about"
    assert document.title == "ECD Organisation"

    assert (
        "We support early childhood development."
        in document.content
    )

    assert "Navigation" not in document.content
    assert "Footer" not in document.content
    assert "console.log" not in document.content
    assert "color: red" not in document.content


def test_extract_document_generates_content_hash():
    html = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <p>ECD information.</p>
        </body>
    </html>
    """

    document = extract_document(
        html=html,
        url="https://example.org",
    )

    expected_hash = calculate_content_hash(
        document.content
    )

    assert document.content_hash == expected_hash


def test_extract_document_rejects_empty_html():
    try:
        extract_document(
            html="",
            url="https://example.org",
        )
    except ValueError as exc:
        assert str(exc) == "HTML content cannot be empty."
    else:
        raise AssertionError(
            "Expected ValueError for empty HTML."
        )


def test_extract_document_rejects_empty_content():
    html = """
    <html>
        <head>
            <title>Empty</title>
        </head>
        <body>
            <script>
                console.log("nothing useful");
            </script>
        </body>
    </html>
    """

    try:
        extract_document(
            html=html,
            url="https://example.org",
        )
    except ValueError as exc:
        assert "No readable content found" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for empty document content."
        )