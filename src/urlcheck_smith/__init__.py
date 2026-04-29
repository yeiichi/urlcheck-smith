from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    "run_extract_https",
]

if TYPE_CHECKING:
    # Avoid importing cli at import-time (cli imports from this module).
    from .cli import run_extract_https as run_extract_https


def __getattr__(name: str) -> Any:
    # Public re-exports that would otherwise introduce import cycles.
    if name == "run_extract_https":
        from .cli import run_extract_https as _run_extract_https

        return _run_extract_https
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + ["run_extract_https"])
