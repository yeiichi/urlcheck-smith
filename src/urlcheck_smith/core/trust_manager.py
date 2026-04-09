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
        # Reloading from disk to pick up any changes (e.g. from editor functions)
        # load_db uses caching/defaults efficiently.
        self._uc_smith_db = load_db(self._db_path)

    def _tier_from_category(self, category: str | None) -> str:
        if category == "government":
            return "TIER_1_OFFICIAL"
        if category in {"education", "news", "standards"}:
            return "TIER_2_RELIABLE"
        if category == "international":
            return "TIER_1_OFFICIAL"
        return "TIER_3_GENERAL"

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

        # v1.7+ metadata-driven priority
        metadata = self._uc_smith_db.get("metadata", {})
        priority = metadata.get("priority", ["user_defined", "api_audit", "global_rules"])

        # Add explicit override as first priority if not specified (legacy behavior)
        if "override" not in priority:
            priority = ["override"] + priority

        for stage in priority:
            # 1. user_defined
            if stage == "user_defined":
                for entry in self._uc_smith_db.get("user_defined", []):
                    entry_name = entry.get("name", "").lower()
                    if entry_name == domain_only or entry_name == hostname or hostname.endswith(f".{entry_name}"):
                        if "trust_tier" in entry:
                            return entry["trust_tier"]
                        return self._tier_from_category(entry.get("category"))

            # 2. global_rules
            elif stage == "global_rules":
                rules = self._uc_smith_db.get("global_rules", [])
                sorted_rules = sorted(rules, key=lambda x: len(x.get("name", "")), reverse=True)
                for rule in sorted_rules:
                    name = rule.get("name", "").lower()
                    if not name:
                        continue
                    if hostname == name or domain_only == name or hostname.endswith(f".{name}"):
                        if "trust_tier" in rule:
                            return rule["trust_tier"]
                        return self._tier_from_category(rule.get("category"))

            # 3. api_audit / discovered_cache
            elif stage == "api_audit":
                for entry in self._uc_smith_db.get("discovered_cache", []):
                    if entry.get("name") == domain_only:
                        score = entry.get("credibility_score", 0.5)
                        if score >= 0.8:
                            return "TIER_1_OFFICIAL"
                        if score >= 0.5:
                            return "TIER_2_RELIABLE"
                        return "TIER_3_GENERAL"

            # 4. explicit override rules
            elif stage == "override":
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
                    if match:
                        return self._tier_from_category(rule.get("category"))

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
