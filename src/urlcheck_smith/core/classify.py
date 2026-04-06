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

logger = logging.getLogger(__name__)

PRESETS = {
    "japan": "rules_japan.yaml",
    "eu": "rules_eu.yaml",
    "global": "rules_global.yaml",
}

class SiteClassifier:
    def __init__(
            self,
            rules_path: Optional[Path | List[Path]] = None,
            preset: Optional[str] = None,
            explain: bool = False,
            normalize_domain: bool = False,
    ) -> None:
        self.explain = explain
        self.normalize_domain = normalize_domain
        
        # Internal rule storage buckets for performance/logic
        self._exact_rules: Dict[str, str] = {}
        self._suffix_rules: List[Tuple[str, str]] = []
        self._regex_rules: List[Tuple[re.Pattern, str]] = []
        
        self._default_category = "private"
        self._default_trust_tier = "TIER_3_GENERAL"

        # 1. Layer: Always load Global as base
        self._load_layer("global", is_preset=True)

        # 2. Layer: Load specific preset if requested
        if preset and preset != "global":
            self._load_layer(preset, is_preset=True)

        # 3. Layer: Load user-defined rules (Highest Priority)
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

    def _load_layer(self, identifier: str, is_preset: bool = True):
        """Loads and parses a YAML layer into the rule buckets."""
        try:
            if is_preset:
                filename = PRESETS.get(identifier, "rules_global.yaml")
                pkg = "urlcheck_smith.data"
                with resources.files(pkg).joinpath(filename).open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
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
                elif "regex" in rule:
                    self._regex_rules.append((re.compile(rule["regex"]), cat))
        except Exception as e:
            logger.error(f"Failed to load rule layer {identifier}: {e}")

    def _get_all_raw_rules(self) -> List[Dict[str, Any]]:
        """Helper to reconstruct rule list for TrustManager/Legacy compat."""
        rules = [{"domain": k, "category": v} for k, v in self._exact_rules.items()]
        rules += [{"suffix": s, "category": c} for s, c in self._suffix_rules]
        return rules

    def _classify_base(self, base: str) -> Tuple[Optional[str], str]:
        # 1. Exact Match (O(1))
        if base in self._exact_rules:
            return base, self._exact_rules[base]
        
        # 2. Longest Suffix Match (Most specific first)
        for suffix, cat in self._suffix_rules:
            if base.endswith(suffix):
                return suffix, cat

        # 3. Regex Match
        for pattern, cat in self._regex_rules:
            if pattern.search(base):
                return pattern.pattern, cat

        return None, self._default_category

    def classify(self, records: Iterable[UrlRecord]) -> List[UrlRecord]:
        out = []
        for r in records:
            parsed = urlparse(r.url)
            base = parsed.netloc.lower()

            matched_pattern, category = self._classify_base(base)

            # Re-create the frozen dataclass with new info
            new = dataclasses.replace(
                r,
                base_url=base,
                category=category,
                trust_tier=self._trust_manager.classify_url(r.url),
            )
            out.append(new)
        return out