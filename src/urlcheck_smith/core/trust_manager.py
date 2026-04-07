import re
from urllib.parse import urlparse
from .update_yaml import load_db

class TrustManager:
    """A General Purpose URL Auditor for urlcheck-smith integration."""

    def __init__(self, override_rules=None, default_tier="TIER_3_GENERAL"):
        self.override_rules = override_rules or []
        self.default_tier = default_tier
        self._uc_smith_db = load_db()

    def classify_url(self, url: str) -> str:
        """Classifies a single URL into a trust tier using rules then fallbacks."""
        parsed = urlparse(url.lower())
        hostname = parsed.netloc

        # Normalize hostname for domain matching
        domain_only = hostname
        if hostname.startswith("www."):
            domain_only = hostname[4:]

        # 0. UC SMITH DB (New Multi-Tiered Database)
        # Check user_defined
        for entry in self._uc_smith_db.get('user_defined', []):
            entry_name = entry.get('name', '').lower()
            if entry_name == domain_only or entry_name == hostname or hostname.endswith(f".{entry_name}"):
                # Use trust_tier from entry if present, else fallback
                if 'trust_tier' in entry:
                    return entry['trust_tier']
                return "TIER_1_OFFICIAL"  # Default for user_defined is high trust
        
        # 33. Check Global Rules (Merged structure)
        rules = self._uc_smith_db.get('global_rules', [])
        # We want to check longer names first to avoid false positives
        sorted_rules = sorted(rules, key=lambda x: len(x.get('name', '')), reverse=True)
        for rule in sorted_rules:
            name = rule.get('name', '').lower()
            if not name: continue
            
            # Use same matching as update_yaml.py
            if hostname == name or domain_only == name or hostname.endswith(f".{name}"):
                if "trust_tier" in rule:
                    return rule["trust_tier"]
                # Default for global_rules if tier not explicitly set
                return "TIER_1_OFFICIAL" if rule.get('category') == 'government' else "TIER_3_GENERAL"

        # Check discovered_cache
        for entry in self._uc_smith_db.get('discovered_cache', []):
            if entry.get('name') == domain_only:
                score = entry.get('credibility_score', 0.5)
                if score >= 0.8: return "TIER_1_OFFICIAL"
                if score >= 0.5: return "TIER_2_RELIABLE"
                return "TIER_3_GENERAL"

        # 2. Check override rules (passed to constructor)
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
