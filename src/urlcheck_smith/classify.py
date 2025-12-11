# src/urlcheck_smith/classify.py
from __future__ import annotations

import dataclasses
from importlib import resources
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import yaml

from .models import UrlRecord

PRESETS = {
    "japan": "rules_japan.yaml",
    "eu": "rules_eu.yaml",
    "global": "rules_global.yaml",
}


class SiteClassifier:
    def __init__(
            self,
            rules_path: Optional[Path] = None,
            preset: Optional[str] = None,
            explain: bool = False,
            normalize_domain: bool = False,
    ) -> None:
        self.explain = explain
        self.normalize_domain = normalize_domain

        if preset:
            filename = PRESETS[preset]
            pkg = "urlcheck_smith.data"
            with resources.files(pkg).joinpath(filename).open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif rules_path:
            text = rules_path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        else:
            pkg = "urlcheck_smith.data"
            with resources.files(pkg).joinpath("site_categories.yaml").open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

        self._rules = data.get("suffix_rules", [])
        self._default_category = data.get("default_category", "private")

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
            )

            if self.explain:
                new.explain = {
                    "matched_suffix": matched_suffix,
                    "category": category,
                }

            out.append(new)
        return out

    def _classify_base(self, base: str):
        for rule in self._rules:
            suffix = rule.get("suffix", "")
            category = rule.get("category", self._default_category)
            if base.endswith(suffix.lower()):
                return suffix, category
        return None, self._default_category
