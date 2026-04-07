# src/urlcheck_smith/core/classify.py
from __future__ import annotations

import dataclasses
import re
import yaml
import logging
from importlib import resources
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

from ..models import UrlRecord
from .trust_manager import TrustManager
from .update_yaml import load_db, enrich_domain

logger = logging.getLogger(__name__)

PRESETS = {}

class SiteClassifier:
    def __init__(
            self,
            rules_path: Optional[Path | List[Path]] = None,
            explain: bool = False,
            normalize_domain: bool = False,
    ) -> None:
        self.explain = explain
        self.normalize_domain = normalize_domain
        
        # Internal rule storage buckets for performance/logic
        self._exact_rules: Dict[str, str] = {}
        self._suffix_rules: List[Tuple[str, str]] = []
        
        self._default_category = "private"
        self._default_trust_tier = "TIER_3_GENERAL"

        # 0. UC SMITH DB (New Multi-Tiered Database)
        self._uc_smith_db = load_db()

        # 1. Layer: Load consolidated rules from UC SMITH DB
        self._load_from_db()

        # 2. Layer: Load user-defined rules (Highest Priority)
        if rules_path:
            paths = [rules_path] if isinstance(rules_path, (str, Path)) else rules_path
            for p in paths:
                self._load_layer(str(p), is_preset=False)

        # Post-processing: Sort suffixes by length (Descending)
        # This ensures 'blog.google.com' matches before 'google.com'
        self._suffix_rules.sort(key=lambda x: len(x[0]), reverse=True)

        self._trust_manager = TrustManager(
            override_rules=self._get_all_raw_rules(),
            default_tier=self._default_trust_tier
        )

    def _load_from_db(self):
        """Loads rules from the internal uc_smith_db."""
        raw_rules = self._uc_smith_db.get("global_rules", [])
        for rule in raw_rules:
            cat = rule.get("category")
            if not cat: continue

            name = rule.get("name", "").lower()
            if not name: continue
            
            # In the new structure, everything is under 'name'.
            # We treat it as a suffix for classification.
            self._suffix_rules.append((name, cat))
        
        # Sort suffix rules by length (Descending) for longest match
        self._suffix_rules.sort(key=lambda x: len(x[0]), reverse=True)

    def _load_layer(self, identifier: str):
        """Loads and parses a YAML layer into the rule buckets."""
        try:
            data = yaml.safe_load(Path(identifier).read_text(encoding="utf-8"))

            if not data:
                return

            # Update defaults if provided in this layer
            self._default_category = data.get("default_category", self._default_category)
            self._default_trust_tier = data.get("default_trust_tier", self._default_trust_tier)

            raw_rules = data.get("rules", data.get("suffix_rules", []))
            for rule in raw_rules:
                cat = rule.get("category")
                if not cat: continue

                if "domain" in rule:
                    # Overwrites existing keys (Layering/Priority)
                    self._exact_rules[rule["domain"].lower()] = cat
                elif "suffix" in rule:
                    self._suffix_rules.append((rule["suffix"].lower(), cat))
        except Exception as e:
            logger.error(f"Failed to load rule layer {identifier}: {e}")

    def _get_all_raw_rules(self) -> List[Dict[str, Any]]:
        """Helper to reconstruct rule list for TrustManager/Legacy compat."""
        rules = [{"domain": k, "category": v} for k, v in self._exact_rules.items()]
        rules += [{"suffix": s, "category": c} for s, c in self._suffix_rules]
        return rules

    def _classify_base(self, base: str) -> Tuple[Optional[str], str]:
        # 0. Load logic with prioritization
        
        # 1. Exact Match (O(1)) - include DB global rules if exact domain
        if base in self._exact_rules:
            return base, self._exact_rules[base]
        
        # 2. UC SMITH DB - user_defined (Exact match)
        for entry in self._uc_smith_db.get('user_defined', []):
            if entry.get('name') == base:
                return base, entry.get('category', 'User-Verified')

        # 3. Longest Suffix Match (Most specific first) - include DB global rules
        for suffix, cat in self._suffix_rules:
            # We want to match if it IS the suffix OR if it's a subdomain of the suffix
            if base == suffix or base.endswith(f".{suffix}"):
                return suffix, cat

        return None, self._default_category

    def classify(self, records: Iterable[UrlRecord]) -> List[UrlRecord]:
        out = []
        for r in records:
            parsed = urlparse(r.url)
            hostname = parsed.netloc.lower()
            
            # Normalize hostname for domain matching
            base = hostname
            if hostname.startswith("www."):
                base = hostname[4:]

            matched_pattern, category = self._classify_base(base)
            
            # If not matched by normalized base, try with full hostname
            if category == self._default_category and base != hostname:
                matched_pattern_full, category_full = self._classify_base(hostname)
                if category_full != self._default_category:
                    matched_pattern, category = matched_pattern_full, category_full

            # Re-create the frozen dataclass with new info
            new = dataclasses.replace(
                r,
                base_url=hostname,
                category=category,
                trust_tier=self._trust_manager.classify_url(r.url),
            )
            out.append(new)
        return out