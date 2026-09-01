from urllib.robotparser import RobotFileParser

from app.services.web_ingestion_service import (
    calculate_content_hash,
    canonicalise_public_url,
    crawl_public_pages,
    extract_document,
    extract_links,
    is_binary_url,
    is_crawlable_url,
    load_robots_txt,
    normalise_text,
)


HOME_HTML = """
<html>
    <head><title>Home | SmartStart Early Learning</title></head>
    <body>
        <nav>Navigation</nav>
        <main>
            <h1>Early Learning for Every Child</h1>
            <p>
                SmartStart is pioneering a social franchise model that
                enables women to run quality early learning programmes.
            </p>
            <a href="/about-us/">About Us</a>
            <a href="/impact/">Impact</a>
            <a href="https://portal.smartstart.org.za/login">Portal</a>
            <a href="/files/briefing-1.pdf">PDF briefing</a>
            <a href="https://example.com/external">External</a>
        </main>
        <footer>Footer</footer>
    </body>
</html>
"""

ABOUT_HTML = """
<html>
    <head><title>About Us | SmartStart</title></head>
    <body>
        <main>
            <p>
                Under our model, implementing partners train franchisees
                to deliver the same evidence-based early learning programme.
                The programme is supported by licensing and quality
                assurance processes implemented by a national team of Coaches.
            </p>
            <a href="/contact-us/">Contact</a>
        </main>
    </body>
</html>
"""

IMPACT_HTML = """
<html>
    <head><title>Impact | SmartStart</title></head>
    <body>
        <main>
            <p>
                SmartStart has connected more than 320,000 children to
                quality early learning during the most critical years.
            </p>
        </main>
    </body>
</html>
"""

CONTACT_HTML = """
<html>
    <head><title>Contact Us | SmartStart</title></head>
    <body>
        <main>
            <p>Contact SmartStart at hello@smartstart.org.za.</p>
        </main>
    </body>
</html>
"""

ROBOTS_TXT = "User-agent: *\nDisallow:\n"


def _pages():
    return {
        "https://smartstart.org.za/robots.txt": ROBOTS_TXT,
        "https://smartstart.org.za/": HOME_HTML,
        "https://smartstart.org.za/about-us/": ABOUT_HTML,
        "https://smartstart.org.za/impact/": IMPACT_HTML,
        "https://smartstart.org.za/contact-us/": CONTACT_HTML,
    }


def fake_fetch(url, timeout=20):
    pages = _pages()
    if url not in pages:
        raise RuntimeError(f"Failed to fetch {url}: HTTP 404")
    return pages[url]


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


def test_canonicalise_rejects_portal_and_external_hosts():
    assert canonicalise_public_url(
        "https://portal.smartstart.org.za/login"
    ) is None
    assert canonicalise_public_url("https://example.com/about") is None
    assert canonicalise_public_url(
        "https://www.smartstart.org.za/about-us/"
    ) == "https://smartstart.org.za/about-us/"


def test_binaries_are_not_crawlable():
    assert is_binary_url("https://smartstart.org.za/files/briefing-1.pdf")
    assert not is_crawlable_url(
        "https://smartstart.org.za/files/briefing-1.pdf"
    )


def test_extract_links_resolves_relative_hrefs():
    links = extract_links(HOME_HTML, "https://smartstart.org.za/")
    assert "https://smartstart.org.za/about-us/" in links
    assert "https://portal.smartstart.org.za/login" in links


def test_crawl_stays_on_public_site_and_skips_portal_and_binaries():
    documents = crawl_public_pages(
        ["https://smartstart.org.za/"],
        max_pages=8,
        fetch_html=fake_fetch,
    )
    urls = {document.url for document in documents}

    assert "https://smartstart.org.za/" in urls
    assert "https://smartstart.org.za/about-us/" in urls
    assert "https://smartstart.org.za/impact/" in urls
    assert not any("portal.smartstart.org.za" in url for url in urls)
    assert not any(url.endswith(".pdf") for url in urls)
    contents = {document.url: document.content for document in documents}
    assert "social franchise model" in contents["https://smartstart.org.za/"]
    assert "evidence-based early learning programme" in contents[
        "https://smartstart.org.za/about-us/"
    ]


def test_crawl_respects_max_pages():
    documents = crawl_public_pages(
        ["https://smartstart.org.za/"],
        max_pages=1,
        fetch_html=fake_fetch,
    )
    assert len(documents) == 1
    assert documents[0].url == "https://smartstart.org.za/"


def test_crawl_skips_failed_pages_without_raising():
    def flaky_fetch(url, timeout=20):
        if url.endswith("robots.txt"):
            return ROBOTS_TXT
        if url.rstrip("/").endswith("about-us"):
            raise RuntimeError("Failed to fetch: HTTP 404")
        return fake_fetch(url, timeout=timeout)

    documents = crawl_public_pages(
        [
            "https://smartstart.org.za/",
            "https://smartstart.org.za/about-us/",
        ],
        max_pages=8,
        fetch_html=flaky_fetch,
    )
    urls = {document.url for document in documents}
    assert "https://smartstart.org.za/about-us/" not in urls
    assert "https://smartstart.org.za/" in urls


def test_robots_txt_disallow_is_respected():
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /about-us"])
    documents = crawl_public_pages(
        ["https://smartstart.org.za/", "https://smartstart.org.za/about-us/"],
        max_pages=8,
        fetch_html=fake_fetch,
        robots_parser=parser,
    )
    urls = {document.url for document in documents}
    assert "https://smartstart.org.za/about-us/" not in urls


def test_load_robots_txt_allows_all_when_fetch_fails():
    def boom(url, timeout=20):
        raise RuntimeError("offline")

    parser = load_robots_txt(fetch_html=boom)
    assert parser.can_fetch("ECD-Intelligence-Platform", "https://smartstart.org.za/")
