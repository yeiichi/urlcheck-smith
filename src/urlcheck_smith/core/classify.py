# src/urlcheck_smith/core/classify.py
from __future__ import annotations

import dataclasses
from importlib import resources
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import re
import yaml

from ..models import UrlRecord
from .trust_manager import TrustManager

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
        """
        Initialize the SiteClassifier.

        Rule precedence:
        1. User-defined rules (from rules_path, last file has highest priority)
        2. Base rules (from preset OR default site_categories.yaml)
        Matching follows a "first-match-wins" strategy.
        """
        self.explain = explain
        self.normalize_domain = normalize_domain

        # Load base rules
        if preset:
            filename = PRESETS[preset]
            pkg = "urlcheck_smith.data"
            with resources.files(pkg).joinpath(filename).open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            pkg = "urlcheck_smith.data"
            with resources.files(pkg).joinpath("site_categories.yaml").open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

        self._rules = data.get("rules", data.get("suffix_rules", []))
        self._default_category = data.get("default_category", "private")
        self._default_trust_tier = data.get("default_trust_tier", "TIER_3_GENERAL")

        # Load and merge user-defined rules
        if rules_path:
            if isinstance(rules_path, (str, Path)):
                paths = [Path(rules_path)]
            else:
                paths = [Path(p) for p in rules_path]

            for p in paths:
                user_data = yaml.safe_load(p.read_text(encoding="utf-8"))
                if user_data:
                    user_rules = user_data.get("rules", user_data.get("suffix_rules", []))
                    # Prepend user rules so they have higher priority
                    self._rules = user_rules + self._rules
                    
                    # Optionally override defaults if specified in user file
                    if "default_category" in user_data:
                        self._default_category = user_data["default_category"]
                    if "default_trust_tier" in user_data:
                        self._default_trust_tier = user_data["default_trust_tier"]

        self._trust_manager = TrustManager(
            override_rules=self._rules,
            default_tier=self._default_trust_tier
        )

    @staticmethod
    def _load_rules(rules_path: Path | None) -> dict:
        if rules_path is not None:
            text = rules_path.read_text(encoding="utf-8")
            return yaml.safe_load(text) or {}

        # Fallback to built-in YAML
        package = "urlcheck_smith.data"
        filename = "site_categories.yaml"
        with resources.files(package).joinpath(filename).open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def classify(self, records: Iterable[UrlRecord]) -> List[UrlRecord]:
        out = []
        for r in records:
            parsed = urlparse(r.url)
            base = parsed.netloc.lower()

            matched_suffix, category = self._classify_base(base)

            new = dataclasses.replace(
                r,
                base_url=base,
                category=category,
                trust_tier=self._trust_manager.classify_url(r.url),
            )

            # Note: if we want to support 'explain', we might need to add it to UrlRecord
            # or use a different mechanism, as UrlRecord is frozen.
            # Currently it seems broken in the original code too if it's frozen.

            out.append(new)
        return out

    def _classify_base(self, base: str):
        # Normalize base by removing common subdomains like 'www.' for domain matching
        domain_only = base
        if base.startswith("www."):
            domain_only = base[4:]

        for rule in self._rules:
            category = rule.get("category")
            if not category:
                continue

            if "domain" in rule:
                target_domain = rule["domain"].lower()
                if base == target_domain or domain_only == target_domain:
                    return rule["domain"], category
            elif "suffix" in rule:
                suffix = rule["suffix"]
                if base.endswith(suffix.lower()):
                    return suffix, category
            elif "regex" in rule:
                if re.search(rule["regex"], base):
                    return rule["regex"], category

        return None, self._default_category
