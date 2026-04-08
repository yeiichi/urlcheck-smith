from __future__ import annotations

from importlib import metadata

_DEFAULT_UA_PREFIX = "UrlCheckSmith"


def get_default_user_agent() -> str:
    """
    Generates the default user agent string for the application.

    This function retrieves the current version of the package using metadata. If the
    package version cannot be determined, it defaults to "dev". The user agent string
    is constructed by concatenating a predefined prefix with the obtained version.

    Returns:
        str: The user agent string.

    Raises:
        metadata.PackageNotFoundError: If the package version cannot be retrieved and
            metadata raises this exception internally. However, this is handled within
            the function, and a fallback version "dev" is used instead.
    """
    try:
        version = metadata.version("urlcheck-smith")
    except metadata.PackageNotFoundError:
        version = "dev"
    return f"{_DEFAULT_UA_PREFIX}/{version}"