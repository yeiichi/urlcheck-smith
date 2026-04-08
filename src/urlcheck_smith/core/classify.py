# src/urlcheck_smith/core/classify.py
from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import yaml

from ..models import UrlRecord
from .trust_manager import TrustManager
from .update_yaml import load_db

logger = logging.getLogger(__name__)

PRESETS = {}

class SiteClassifier:
    def __init__(
            self,
            rules_path: Optional[Path | List[Path]] = None,
            explain: bool = False,
            normalize_domain: bool = False,
            db_path: str | Path | None = None,
    ) -> None:
        self.explain = explain
        self.normalize_domain = normalize_domain
        self._db_path = Path(db_path) if db_path is not None else None

        # Internal rule storage buckets for performance/logic
        self._exact_rules: Dict[str, str] = {}
        self._suffix_rules: List[Tuple[str, str]] = []

        self._default_category = "private"
        self._default_trust_tier = "TIER_3_GENERAL"

        # Load DB using explicit path if provided, otherwise default resolution
        self._uc_smith_db = load_db(self._db_path)

        # Load consolidated rules from UC Smith DB
        self._load_from_db()

        # Load user-defined rules (highest priority)
        if rules_path:
            paths = [rules_path] if isinstance(rules_path, (str, Path)) else rules_path
            for p in paths:
                self._load_layer(str(p))

        # Ensure longest suffix wins
        self._suffix_rules.sort(key=lambda x: len(x[0]), reverse=True)

        self._trust_manager = TrustManager(
            override_rules=self._get_all_raw_rules(),
            default_tier=self._default_trust_tier,
            db_path=self._db_path,
        )

    def _load_from_db(self):
        """Loads rules from the internal uc_smith_db."""
        raw_rules = self._uc_smith_db.get("global_rules", [])
        for rule in raw_rules:
            cat = rule.get("category")
            if not cat:
                continue

            name = rule.get("name", "").lower()
            if not name:
                continue

            self._suffix_rules.append((name, cat))

        self._suffix_rules.sort(key=lambda x: len(x[0]), reverse=True)

    def _load_layer(self, identifier: str):
        """Loads and parses a YAML layer into the rule buckets."""
        try:
            data = yaml.safe_load(Path(identifier).read_text(encoding="utf-8"))

            if not data:
                return

            self._default_category = data.get("default_category", self._default_category)
            self._default_trust_tier = data.get("default_trust_tier", self._default_trust_tier)

            raw_rules = data.get("rules", data.get("suffix_rules", []))
            for rule in raw_rules:
                cat = rule.get("category")
                if not cat:
                    continue

                if "domain" in rule:
                    self._exact_rules[rule["domain"].lower()] = cat
                elif "suffix" in rule:
                    self._suffix_rules.append((rule["suffix"].lower(), cat))
        except Exception as e:
            logger.error(f"Failed to load rule layer {identifier}: {e}")

    def _get_all_raw_rules(self) -> List[Dict[str, Any]]:
        """Helper to reconstruct rule list for TrustManager/legacy compat."""
        rules = [{"domain": k, "category": v} for k, v in self._exact_rules.items()]
        rules += [{"suffix": s, "category": c} for s, c in self._suffix_rules]
        return rules

    def _classify_base(self, base: str) -> Tuple[Optional[str], str]:
        # 1. Exact match
        if base in self._exact_rules:
            return base, self._exact_rules[base]

        # 2. User-defined exact match
        for entry in self._uc_smith_db.get("user_defined", []):
            if entry.get("name") == base:
                return base, entry.get("category", "User-Verified")

        # 3. Longest suffix match
        for suffix, cat in self._suffix_rules:
            if base == suffix or base.endswith(f".{suffix}"):
                return suffix, cat

        return None, self._default_category

    def classify(self, records: Iterable[UrlRecord]) -> List[UrlRecord]:
        out = []
        for r in records:
            parsed = urlparse(r.url)
            hostname = parsed.netloc.lower()

            base = hostname[4:] if hostname.startswith("www.") else hostname

            matched_pattern, category = self._classify_base(base)

            explain_msg = None
            if category == self._default_category and base != hostname:
                matched_pattern_full, category_full = self._classify_base(hostname)
                if category_full != self._default_category:
                    matched_pattern, category = matched_pattern_full, category_full

            if self.explain:
                if matched_pattern:
                    explain_msg = f"Matched pattern '{matched_pattern}' -> category '{category}'"
                else:
                    explain_msg = f"No match found. Using default category '{category}'"

            new = dataclasses.replace(
                r,
                base_url=hostname,
                category=category,
                trust_tier=self._trust_manager.classify_url(r.url),
                explain=explain_msg,
            )
            out.append(new)
        return out