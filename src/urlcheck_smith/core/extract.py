# src/urlcheck_smith/core/extract.py
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Iterable, List, Set, Iterator
from urllib.parse import urlparse, urlunparse

HTTPS_URL_RE = re.compile(r"https://[^\s,\"'<>]+", re.IGNORECASE)

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(levelname)s: %(message)s",
# )

from urlextract import URLExtract

from ..models import UrlRecord

# Initialize the extractor once. 
# It handles TLD updates and complex character matching internally.
_EXTRACTOR = URLExtract()


def normalize_url(url: str) -> str:
    """
    Standardize the URL to prevent duplicate checks of the same resource.
    """
    try:
        # urlextract might return URLs with trailing punctuation if not careful.
        # We strip common trailing noise before parsing.
        url = url.rstrip('.,);]')

        # urlextract might return URLs without schemes (e.g., 'google.com').
        # urlparse needs a scheme to identify the netloc correctly.
        temp_url = url if "://" in url else f"http://{url}"
        parsed = urlparse(temp_url)

        netloc = parsed.netloc.lower()
        if not netloc:
            return url

        normalized = urlunparse((
            parsed.scheme.lower() or "http",
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Dropping fragments
        ))
        return normalized.rstrip('/')
    except Exception:
        return url


def extract_urls_from_text(text: str) -> List[UrlRecord]:
    """
    Extract, clean, and deduplicate URLs from a block of text using urlextract.
    """
    # urlextract handles trailing punctuation and balanced brackets automatically.
    found = _EXTRACTOR.find_urls(text, only_unique=True)

    seen: Set[str] = set()
    records: List[UrlRecord] = []

    for raw in found:
        normalized = normalize_url(raw)
        if normalized not in seen:
            seen.add(normalized)
            records.append(UrlRecord(url=normalized))

    return records


def stream_extract_from_file(path: Path) -> Iterator[UrlRecord]:
    """
    Generator that yields URLs line-by-line to handle large files efficiently.
    """
    seen: Set[str] = set()
    try:
        with path.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # We use the internal extractor logic per line
                for record in extract_urls_from_text(line):
                    if record.url not in seen:
                        seen.add(record.url)
                        yield record
    except (OSError, UnicodeDecodeError):
        return


def extract_urls_from_paths(paths: Iterable[Path]) -> List[UrlRecord]:
    """
    Aggregates URLs from multiple paths using the streaming logic.
    """
    all_records: List[UrlRecord] = []
    global_seen: Set[str] = set()

    for p in paths:
        for record in stream_extract_from_file(p):
            if record.url not in global_seen:
                global_seen.add(record.url)
                all_records.append(record)

    return all_records  # import logging


def extract_https_urls(path: Path) -> list[str]:
    """
    Extracts unique HTTPS URLs from a file. Insecure HTTP links are ignored.

    This function reads the content of a file from the provided path, extracts all
    HTTP and HTTPS URLs using a predefined regular expression, cleans the URLs by
    removing trailing characters such as '.', ',', ')', ']', '>', or quotation marks,
    removes duplicates, and returns a sorted list of unique URLs.
    This script is made CLI-apps-friendly; e.g., a manual input string will be converted
    to a Path object to avoid raising errors.

    Args:
        path (Path): The path to the file to be processed.

    Returns:
        list[str]: A sorted list of unique cleaned HTTP and HTTPS URLs extracted
        from the file.
    """
    # logging.info("Reading file: %s", path)

    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")

    raw_urls = HTTPS_URL_RE.findall(text)
    # logging.info("Regex HTTP(S) matches: %d", len(raw_urls))

    cleaned = [
        url.strip().rstrip('.,);]>"\'')
        for url in raw_urls
    ]
    # logging.info("After cleaning: %d", len(cleaned))

    unique_urls = sorted(set(cleaned))
    # logging.info("After dedupe: %d", len(unique_urls))

    return unique_urls


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def urls_to_csv(urls: list[str], output_path: Path) -> None:
    """
    Save the URL list to a CSV file with columns:
    - URL
    - hashed_URL (SHA-256 hex)

    Args:
        urls (list[str]): List of URLs
        output_path (Path): Output CSV file path
    """
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # header
        writer.writerow(["URL", "hashed_URL"])

        # rows
        for url in urls:
            writer.writerow([url, sha256_hex(url)])
