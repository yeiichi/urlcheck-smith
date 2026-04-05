import re
from urllib.parse import urlparse

# --- GLOBAL PATTERNS ---
OFFICIAL_PATTERNS = [
    r"\.gov$",  # US/Global Gov
    r"\.gov\.[a-z]{2}$",  # Country-code Gov (uk, in, br)
    r"\.go\.[a-z]{2}$",  # Japan/Korea/Africa (jp, kr, ke)
    r"\.gob\.[a-z]{2}$",  # Spanish (mx, es)
    r"\.gouv\.[a-z]{2}$",  # French (fr, qc.ca handled differently)
    r"\.un\.org$",  # Official UN
    r"\.europa\.eu$"  # Official EU
]

NEWS_PATTERNS = [
    r"reuters\.com", r"apnews\.com", r"afp\.com",
    r"bbc\.(co\.uk|com)", r"nikkei\.com", r"dw\.com",
    r"nytimes\.com", r"wsj\.com", r"theguardian\.com"
]


class OfficialAuditor:
    """
    Validates whether a given URL belongs to an official domain based on predefined patterns.

    This class provides functionality to inspect and validate if a URL corresponds to
    an official source by matching it against a set of predefined patterns defining
    trusted domains.

    Methods:
        is_official(url: str) -> bool: Checks if a URL belongs to a predefined set of
        official domains.
    """
    def is_official(self, url: str) -> bool:
        try:
            # Step 1: Parse the URL to get ONLY the hostname
            # This stops 'malicious.com/search?q=gov.uk' from matching
            parsed = urlparse(url.lower())
            hostname = parsed.netloc
            # Step 2: Ensure we are matching the ACTUAL end of the domain
            return any(re.search(p, hostname) for p in OFFICIAL_PATTERNS)
        except Exception:
            return False


class NewsAuditor:
    def is_news(self, url: str) -> bool:
        return any(re.search(p, url.lower()) for p in NEWS_PATTERNS)


class TrustManager:
    """A General Purpose URL Auditor for urlcheck-smith integration."""

    def __init__(self):
        self.official_auditor = OfficialAuditor()
        self.news_auditor = NewsAuditor()

    def classify_url(self, url: str) -> str:
        """Classifies a single URL into a trust tier."""
        if self.official_auditor.is_official(url):
            return "TIER_1_OFFICIAL"
        if self.news_auditor.is_news(url):
            return "TIER_2_NEWS"
        return "TIER_3_GENERAL"

    def audit_list(self, url_list: list) -> dict:
        """Processes a list of raw URLs into a categorized report."""
        report = {"official": [], "news": [], "general": []}
        for url in url_list:
            category = self.classify_url(url)
            if category == "TIER_1_OFFICIAL":
                report["official"].append(url)
            elif category == "TIER_2_NEWS":
                report["news"].append(url)
            else:
                report["general"].append(url)
        return report
