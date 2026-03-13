from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class UrlRecord:
    url: str
    base_url: Optional[str] = None
    category: str = "unknown"
    http_status: Optional[int] = None
    redirected_url: Optional[str] = None
    human_check_suspected: bool = False
    soft_404_detected: bool = False
    trust_tier: str = "TIER_3_GENERAL"
    error: Optional[str] = None
