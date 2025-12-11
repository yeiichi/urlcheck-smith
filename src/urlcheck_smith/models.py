from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class UrlRecord:
    """
    The core record passed through the MVP pipeline.

    Stages:
      - extract: url
      - classify: base_url, category
      - check: http_status, redirected_url, error, human_check_suspected
    """
    url: str
    base_url: Optional[str] = None
    category: Optional[str] = None
    http_status: Optional[int] = None
    redirected_url: Optional[str] = None
    error: Optional[str] = None
    human_check_suspected: bool = False
    explain: Optional[dict] = None
