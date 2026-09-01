#!/usr/bin/env python3
"""Ingest the public SmartStart website into the organisation knowledge base.

The crawler stays on https://smartstart.org.za/, respects robots.txt, skips
the login portal, and caps the number of pages. Live crawl can be skipped:

    uv run python scripts/ingest_smartstart.py --skip
    SMARTSTART_INGEST_SKIP=1 uv run python scripts/ingest_smartstart.py

Network failures are offline-safe by default so local/dev setup can proceed
without smartstart.org.za being reachable.
"""

from __future__ import annotations

import argparse
import json
import sys

from app.database.database import SessionLocal
from app.services.smartstart_ingestion_service import (
    SMARTSTART_SEED_URLS,
    ingest_smartstart_website,
)
from app.services.web_ingestion_service import DEFAULT_MAX_PAGES, DEFAULT_TIMEOUT


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest public SmartStart marketing pages into pgvector "
            "for one organisation."
        )
    )
    parser.add_argument(
        "--organisation-id",
        type=int,
        default=1,
        help="Target organisation (default: 1, the seeded org).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum HTML pages to crawl (default: {DEFAULT_MAX_PAGES}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Skip live crawl (also honours SMARTSTART_INGEST_SKIP).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if the live crawl cannot run (default is offline-safe).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db = SessionLocal()
    try:
        summary = ingest_smartstart_website(
            db,
            args.organisation_id,
            skip=args.skip,
            offline_safe=not args.strict,
            max_pages=args.max_pages,
            timeout=args.timeout,
            seed_urls=SMARTSTART_SEED_URLS,
        )
    except Exception as exc:
        print(f"SmartStart ingest failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(json.dumps(summary, indent=2))
    if summary.get("skipped"):
        print(summary.get("reason") or "SmartStart ingest skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
