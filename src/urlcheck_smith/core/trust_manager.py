import re
from urllib.parse import urlparse

# --- GLOBAL PATTERNS (Fallback) ---
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
    r"nytimes\.com", r"wsj\.com", r"theguardian\.com",
    r"asahi\.com", r"yomiuri\.co\.jp"
]


class OfficialAuditor:
    """
    Validates whether a given URL belongs to an official domain based on predefined patterns.
    """
    def is_official(self, url: str) -> bool:
        try:
            parsed = urlparse(url.lower())
            hostname = parsed.netloc
            return any(re.search(p, hostname) for p in OFFICIAL_PATTERNS)
        except Exception:
            return False


class NewsAuditor:
    def is_news(self, url: str) -> bool:
        try:
            parsed = urlparse(url.lower())
            hostname = parsed.netloc
            return any(re.search(p, hostname) for p in NEWS_PATTERNS)
        except Exception:
            return False


class TrustManager:
    """A General Purpose URL Auditor for urlcheck-smith integration."""

    def __init__(self, override_rules=None, default_tier="TIER_3_GENERAL"):
        self.official_auditor = OfficialAuditor()
        self.news_auditor = NewsAuditor()
        self.override_rules = override_rules or []
        self.default_tier = default_tier

    def classify_url(self, url: str) -> str:
        """Classifies a single URL into a trust tier using rules then fallbacks."""
        parsed = urlparse(url.lower())
        hostname = parsed.netloc

        # Normalize hostname for domain matching
        domain_only = hostname
        if hostname.startswith("www."):
            domain_only = hostname[4:]

        # 1. Check override rules (from YAML)
        for rule in self.override_rules:
            match = False
            if "domain" in rule:
                target_domain = rule["domain"].lower()
                if hostname == target_domain or domain_only == target_domain:
                    match = True
            elif "suffix" in rule:
                if hostname.endswith(rule["suffix"].lower()):
                    match = True
            elif "regex" in rule:
                if re.search(rule["regex"], hostname):
                    match = True

            if match and "trust_tier" in rule:
                return rule["trust_tier"]

        # 2. Fallback to hardcoded patterns if no override matched
        if self.official_auditor.is_official(url):
            return "TIER_1_OFFICIAL"
        if self.news_auditor.is_news(url):
            return "TIER_2_RELIABLE"

        return self.default_tier

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
