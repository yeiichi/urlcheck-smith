from __future__ import annotations

from importlib import metadata

_DEFAULT_UA_PREFIX = "UrlCheckSmith"


def get_default_user_agent() -> str:
    try:
        version = metadata.version("urlcheck-smith")
    except metadata.PackageNotFoundError:
        version = "dev"
    return f"{_DEFAULT_UA_PREFIX}/{version}"