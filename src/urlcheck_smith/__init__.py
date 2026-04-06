from __future__ import annotations

from .core.check import check_urls
from .core.classify import SiteClassifier
from .core.extract import extract_urls_from_paths, extract_urls_from_text, stream_extract_from_file
from .core.trust_manager import TrustManager
from .models import UrlRecord

__all__ = [
    "check_urls",
    "SiteClassifier",
    "TrustManager",
    "UrlRecord",
    "stream_extract_from_file",
    "extract_urls_from_paths",
    "extract_urls_from_text",
]