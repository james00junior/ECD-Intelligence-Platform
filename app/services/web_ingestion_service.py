from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = (
    "ECD-Intelligence-Platform/0.1 "
    "(public knowledge ingestion)"
)


@dataclass(frozen=True)
class WebDocument:
    """Normalised content extracted from a public web page."""

    url: str
    title: str
    content: str
    content_hash: str


def fetch_url(
    url: str,
    timeout: int = 20,
    user_agent: str = DEFAULT_USER_AGENT,
) -> str:
    """
    Fetch a public web page.

    Only HTTP GET requests are performed.
    """

    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(
                charset,
                errors="replace",
            )

    except HTTPError as exc:
        raise RuntimeError(
            f"Failed to fetch {url}: HTTP {exc.code}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Failed to fetch {url}: {exc.reason}"
        ) from exc


def extract_document(
    html: str,
    url: str,
) -> WebDocument:
    """
    Extract readable text and metadata from HTML.

    Navigation, scripts, styles and other non-content elements
    are removed before normalisation.
    """

    if not html or not html.strip():
        raise ValueError("HTML content cannot be empty.")

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
        ]
    ):
        element.decompose()

    title = ""

    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    content_root = soup.body or soup

    text = content_root.get_text(
        separator=" ",
        strip=True,
    )

    content = normalise_text(text)

    if not content:
        raise ValueError(
            f"No readable content found at {url}."
        )

    content_hash = calculate_content_hash(content)

    return WebDocument(
        url=url,
        title=title or url,
        content=content,
        content_hash=content_hash,
    )


def normalise_text(text: str) -> str:
    """
    Normalise extracted web text.

    Collapses repeated whitespace while preserving readable
    paragraph-like separation where possible.
    """

    text = unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def calculate_content_hash(content: str) -> str:
    """
    Generate a deterministic SHA-256 hash for document content.
    """

    if not content:
        raise ValueError(
            "Cannot calculate a content hash for empty content."
        )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def ingest_url(
    url: str,
    timeout: int = 20,
) -> WebDocument:
    """
    Fetch and normalise a public web page.
    """

    html = fetch_url(
        url=url,
        timeout=timeout,
    )

    return extract_document(
        html=html,
        url=url,
    )