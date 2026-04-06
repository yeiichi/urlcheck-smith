# src/urlcheck_smith/core/extract.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Set, Iterator
from urllib.parse import urlparse, urlunparse

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
                
    return all_records