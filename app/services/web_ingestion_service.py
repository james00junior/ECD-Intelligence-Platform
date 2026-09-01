from __future__ import annotations

import hashlib
import re
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = (
    "ECD-Intelligence-Platform/0.1 "
    "(public knowledge ingestion)"
)
ROBOTS_USER_AGENT = "ECD-Intelligence-Platform"
PUBLIC_SITE_NETLOCS = frozenset({
    "smartstart.org.za",
    "www.smartstart.org.za",
})
BLOCKED_SITE_NETLOCS = frozenset({
    "portal.smartstart.org.za",
})
BINARY_EXTENSIONS = frozenset({
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".mp3",
    ".mp4",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
})
DEFAULT_MAX_PAGES = 12
DEFAULT_TIMEOUT = 20
ROBOTS_URL = "https://smartstart.org.za/robots.txt"


FetchHtml = Callable[..., str]


@dataclass(frozen=True)
class WebDocument:
    """Normalised content extracted from a public web page."""

    url: str
    title: str
    content: str
    content_hash: str


def fetch_url(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
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
            "Accept": "text/html,application/xhtml+xml,text/plain",
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
    timeout: int = DEFAULT_TIMEOUT,
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


def canonicalise_public_url(url: str) -> str | None:
    """Return a canonical public SmartStart URL, or None if off-site."""

    if not url or not url.strip():
        return None

    url, _fragment = urldefrag(url.strip())
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        return None

    netloc = parsed.netloc.lower().split(":", 1)[0]
    if netloc in BLOCKED_SITE_NETLOCS:
        return None
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if netloc not in {"smartstart.org.za"}:
        return None

    path = parsed.path or "/"
    return urlunparse(("https", netloc, path, "", "", ""))


def is_binary_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(extension) for extension in BINARY_EXTENSIONS)


def is_public_site_url(url: str) -> bool:
    return canonicalise_public_url(url) is not None


def is_crawlable_url(url: str) -> bool:
    if not is_public_site_url(url):
        return False
    return not is_binary_url(url)


def extract_links(html: str, base_url: str) -> list[str]:
    """Extract absolute hrefs from a page without mutating the source HTML."""

    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        links.append(urljoin(base_url, href))

    return links


def looks_like_html(content: str) -> bool:
    if not content or not content.strip():
        return False
    lowered = content.lstrip().lower()
    return any(
        marker in lowered
        for marker in ("<html", "<!doctype html", "<body", "<main", "<p", "<div")
    )


def load_robots_txt(
    fetch_html: FetchHtml | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> RobotFileParser:
    """Load robots.txt, allowing the public site if it cannot be fetched."""

    fetch_html = fetch_html or fetch_url
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)

    try:
        body = fetch_html(ROBOTS_URL, timeout=timeout)
        parser.parse(body.splitlines())
    except TypeError:
        try:
            body = fetch_html(ROBOTS_URL)
            parser.parse(body.splitlines())
        except Exception:
            parser.parse(["User-agent: *", "Disallow:"])
    except Exception:
        parser.parse(["User-agent: *", "Disallow:"])

    return parser


def _fetch_page(fetch_html: FetchHtml, url: str, timeout: int) -> str:
    try:
        return fetch_html(url, timeout=timeout)
    except TypeError:
        return fetch_html(url)


def crawl_public_pages(
    seed_urls: Sequence[str],
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout: int = DEFAULT_TIMEOUT,
    fetch_html: FetchHtml | None = None,
    robots_parser: RobotFileParser | None = None,
) -> list[WebDocument]:
    """
    Crawl a bounded set of public SmartStart marketing pages.

    Stays on smartstart.org.za, skips the login portal and binaries,
    and respects robots.txt. Failed page fetches are skipped.
    """

    fetch_html = fetch_html or fetch_url

    if max_pages <= 0:
        return []

    if robots_parser is None:
        robots_parser = load_robots_txt(
            fetch_html=fetch_html,
            timeout=timeout,
        )

    seen: set[str] = set()
    queue: deque[str] = deque()
    documents: list[WebDocument] = []

    for seed in seed_urls:
        canonical = canonicalise_public_url(seed)
        if canonical and canonical not in seen:
            queue.append(canonical)
            seen.add(canonical)

    while queue and len(documents) < max_pages:
        url = queue.popleft()
        if not is_crawlable_url(url):
            continue
        if not robots_parser.can_fetch(ROBOTS_USER_AGENT, url):
            continue

        try:
            html = _fetch_page(fetch_html, url, timeout)
        except Exception:
            continue

        if not looks_like_html(html):
            continue

        try:
            document = extract_document(html=html, url=url)
        except ValueError:
            continue

        documents.append(document)

        for link in extract_links(html, url):
            canonical = canonicalise_public_url(link)
            if (
                canonical
                and canonical not in seen
                and is_crawlable_url(canonical)
            ):
                seen.add(canonical)
                queue.append(canonical)

    return documents
