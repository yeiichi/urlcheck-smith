Changelog
=========

0.5.0 (2026-04-07)
------------------
- Updated minimum Python version requirement to 3.10+ (removing support for 3.8 and 3.9).
- Modernized type hints (PEP 585 lowercase generics, PEP 604 union types) across the codebase.
- Significant documentation overhaul in `docs/source` to better align with `README.md`.
- Added UC Smith credibility database (`ucsmith_db.yaml`) for multi-tiered trust classification.
- Integrated UC Smith database into `SiteClassifier` and `TrustManager`.
- Removed legacy regex-based classification logic and hardcoded patterns.
- Refactored `TrustManager` to rely on the unified credibility database.
- Added new `db` CLI command to manage and enrich the credibility database.
- Improved `update_yaml.py` to handle package-relative data files.

0.4.0 (2026-04-06)
------------------
- Refactor core logic to modernize and improve URL extraction.
- Replace manual regex with `urlextract` for more robust URL discovery and normalization.
- Implement layered rule loading (global, preset, user) in `SiteClassifier`.
- Optimize classification with exact match lookups and longest-suffix matching.
- Add streaming support for large files in the extraction engine to handle larger datasets efficiently.

0.3.1 (2026-04-05)
------------------
- Package layout refactor for better organization.
- Initial Sphinx documentation setup.
- Updated version metadata and test adjustments for reorganized structure.

0.3.0 (2026-04-05)
------------------
- Added top-level package exports for key components (`check_urls`, `SiteClassifier`, etc.).
- Initial documentation setup with Sphinx.
- Support for Japan, EU, and global rule presets.
- Soft 404 detection and Trust Tier classification.
- CSV and JSONL output formats.
- Support for merging multiple user-defined YAML rule files with precedence handling.
