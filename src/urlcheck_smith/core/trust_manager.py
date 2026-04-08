from pathlib import Path
from urllib.parse import urlparse

from .update_yaml import load_db


class TrustManager:
    """A General Purpose URL Auditor for urlcheck-smith integration."""

    def __init__(self, override_rules=None, default_tier="TIER_3_GENERAL", db_path=None):
        self.override_rules = override_rules or []
        self.default_tier = default_tier
        self._db_path = Path(db_path) if db_path is not None else None
        self._uc_smith_db = load_db(self._db_path)

    def _reload(self):
        # Only reload if we are using the default resolution or the file might have changed.
        # For simplicity, we always reload as it was before, but ensuring load_db is used.
        self._uc_smith_db = load_db(self._db_path)

    def classify_url(self, url: str) -> str:
        """Classifies a single URL into a trust tier using rules then fallbacks."""
        normalized_url = url.lower()
        if "://" not in normalized_url:
            normalized_url = f"http://{normalized_url}"

        parsed = urlparse(normalized_url)
        hostname = parsed.netloc

        # Normalize hostname for domain matching
        domain_only = hostname[4:] if hostname.startswith("www.") else hostname

        self._reload()

        # 1. UC SMITH DB user_defined
        for entry in self._uc_smith_db.get("user_defined", []):
            entry_name = entry.get("name", "").lower()
            if entry_name == domain_only or entry_name == hostname or hostname.endswith(f".{entry_name}"):
                if "trust_tier" in entry:
                    return entry["trust_tier"]
                return "TIER_1_OFFICIAL"

        # 2. UC SMITH DB global rules
        rules = self._uc_smith_db.get("global_rules", [])
        sorted_rules = sorted(rules, key=lambda x: len(x.get("name", "")), reverse=True)
        for rule in sorted_rules:
            name = rule.get("name", "").lower()
            if not name:
                continue

            if hostname == name or domain_only == name or hostname.endswith(f".{name}"):
                if "trust_tier" in rule:
                    return rule["trust_tier"]
                return "TIER_1_OFFICIAL" if rule.get("category") == "government" else "TIER_3_GENERAL"

        # 3. discovered_cache
        for entry in self._uc_smith_db.get("discovered_cache", []):
            if entry.get("name") == domain_only:
                score = entry.get("credibility_score", 0.5)
                if score >= 0.8:
                    return "TIER_1_OFFICIAL"
                if score >= 0.5:
                    return "TIER_2_RELIABLE"
                return "TIER_3_GENERAL"

        # 4. explicit override rules
        for rule in self.override_rules:
            match = False
            if "domain" in rule:
                target_domain = rule["domain"].lower()
                if hostname == target_domain or domain_only == target_domain:
                    match = True
            elif "suffix" in rule:
                if hostname.endswith(rule["suffix"].lower()):
                    match = True

            if match and "trust_tier" in rule:
                return rule["trust_tier"]

        return self.default_tier

    def audit_list(self, url_list: list) -> dict:
        """Processes a list of raw URLs into a categorized report."""
        report = {"official": [], "reliable": [], "general": []}
        for url in url_list:
            category = self.classify_url(url)
            if category == "TIER_1_OFFICIAL":
                report["official"].append(url)
            elif category == "TIER_2_RELIABLE":
                report["reliable"].append(url)
            else:
                report["general"].append(url)
        return report
