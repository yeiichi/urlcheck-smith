from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class UrlRecord:
    """
    Represents a URL record with associated metadata.

    This class is used to store and manage information about a URL, including its
    category, HTTP status, redirection details, and other metadata. The class is
    immutable and can be utilized for analysis, categorization, or tracking of URL
    details.

    Attributes:
        url (str): The URL being recorded.
        base_url (Optional[str]): The base URL from which the `url` is derived, if any.
        category (str): The category assigned to the URL. Defaults to "unknown".
        http_status (Optional[int]): The HTTP status code obtained from the URL, if
            available.
        redirected_url (Optional[str]): The URL to which the original URL redirects, if any.
        human_check_suspected (bool): Indicates whether a human check or challenge
            was suspected while accessing the URL. Defaults to False.
        soft_404_detected (bool): Indicates whether a soft 404 error was detected for
            the URL. Defaults to False.
        trust_tier (str): The trust level assigned to the URL, defaulting to
            "TIER_3_GENERAL".
        error (Optional[str]): Additional information about errors encountered while
            accessing or processing the URL, if any.
        explain (Optional[str]): An explanation or metadata describing additional
            details about the URL, if available.
    """
    url: str
    base_url: Optional[str] = None
    category: str = "unknown"
    http_status: Optional[int] = None
    redirected_url: Optional[str] = None
    human_check_suspected: bool = False
    soft_404_detected: bool = False
    trust_tier: str = "TIER_3_GENERAL"
    error: Optional[str] = None
    explain: Optional[str] = None
