from __future__ import annotations

import dataclasses
from typing import Iterable, List, Optional

import requests

from .models import UrlRecord


def _guess_human_check(content_snippet: str) -> bool:
    """
    VERY rough heuristic to flag potential 'human check' / CAPTCHA pages.
    MVP: simple keyword search in a short snippet.
    """
    lowered = content_snippet.lower()
    keywords = [
        "captcha",
        "are you a robot",
        "unusual traffic",
        "verify you are human",
    ]
    return any(k in lowered for k in keywords)


def check_urls(
    records: Iterable[UrlRecord],
    timeout: float = 5.0,
    user_agent: Optional[str] = None,
) -> List[UrlRecord]:
    """
    Perform a minimal HTTP GET check for each URL.

    For MVP we:
      - follow redirects
      - capture http_status
      - keep final URL
      - grab a small body snippet to guess human-check/CAPTCHA-ish behavior
    """
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    output: List[UrlRecord] = []

    for rec in records:
        try:
            resp = requests.get(
                rec.url,
                timeout=timeout,
                allow_redirects=True,
                headers=headers or None,
            )
            status = resp.status_code
            final_url = resp.url
            snippet = resp.text[:2000] if isinstance(resp.text, str) else ""
            hc = _guess_human_check(snippet)

            new_rec = dataclasses.replace(
                rec,
                http_status=status,
                redirected_url=final_url,
                error=None,
                human_check_suspected=hc,
            )
        except Exception as exc:  # noqa: BLE001 (MVP)
            new_rec = dataclasses.replace(
                rec,
                http_status=None,
                redirected_url=None,
                error=str(exc),
                human_check_suspected=False,
            )

        output.append(new_rec)

    return output
