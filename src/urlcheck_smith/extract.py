# src/urlcheck_smith/extract.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from .models import UrlRecord

# Very simple HTTP(S) detector for MVP.
# Added ',' to the excluded characters to prevent capturing trailing CSV fields.
URL_REGEX = re.compile(r"https?://[^\s<>'\"()\[\],]+")

# Characters that often trail URLs in prose (sentences, lists, etc.)
_TRAILING_PUNCTUATION = ".,);]'\"/"


def extract_urls_from_text(text: str) -> List[UrlRecord]:
    """
    Extract URLs from arbitrary text and return deduplicated UrlRecord list.
    """
    raw_urls = URL_REGEX.findall(text)
    seen = set()
    records: List[UrlRecord] = []

    for u in raw_urls:
        # Strip punctuation that is very likely to be sentence/formatting noise.
        cleaned = u.rstrip(_TRAILING_PUNCTUATION)
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            records.append(UrlRecord(url=cleaned))

    return records


def extract_urls_from_file(path: Path) -> List[UrlRecord]:
    """
    Treat the file as plain text (CSV/JSON/etc. are OK for MVP).
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    return extract_urls_from_text(text)


def extract_urls_from_paths(paths: Iterable[Path]) -> List[UrlRecord]:
    """
    Extract URLs from multiple files, returning a single deduped list.
    """
    all_records: List[UrlRecord] = []
    seen = set()
    for p in paths:
        for rec in extract_urls_from_file(p):
            if rec.url not in seen:
                seen.add(rec.url)
                all_records.append(rec)
    return all_records
