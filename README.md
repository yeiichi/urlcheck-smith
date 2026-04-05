# urlcheck-smith

[![GitHub](https://img.shields.io/badge/GitHub-yeiichi%2Furlcheck--smith-181717?logo=github)](https://github.com/yeiichi/urlcheck-smith)
[![PyPI version](https://img.shields.io/pypi/v/urlcheck-smith.svg)](https://pypi.org/project/urlcheck-smith/)
![Python versions](https://img.shields.io/pypi/pyversions/urlcheck-smith.svg)
![Status](https://img.shields.io/badge/status-Alpha-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

A compact, fast URL analysis pipeline:

- Extract URLs from arbitrary text files  
- Classify domains using suffix-based “site runner” rules (government, edu, private, etc.)
- Trust Tier classification (Official, News, General)
- Optional HTTP checks (status, redirect, CAPTCHA/human-check heuristic)
- Output results as CSV or JSONL
- Standalone URL classifier (`classify-url`)
- Batch classification mode (`classify`)
- Supports rule presets (Japan/EU/global), custom YAML rules, explain mode, quiet mode
- **Classification**: Assigns categories (e.g., government, education) based on domain suffix rules.
- **HTTP Verification**: Checks reachability and captures status codes.
- **Soft 404 Detection**: Identifies pages that return a `200 OK` status but contain "Page Not Found" text.
- **Trust Tier Analysis**: Automatically categorizes URLs into `TIER_1_OFFICIAL`, `TIER_2_NEWS`, or `TIER_3_GENERAL` using `TrustManager`.
- **Human-Check Detection**: Flags URLs that likely lead to CAPTCHA or bot-detection screens.

---

## Features in Detail

### Soft 404 Detection
Many websites are configured to return a standard `200 OK` status even when a page is missing, often displaying a custom "not found" message to users. `urlcheck-smith` detects this by scanning the first 2000 characters of the response for common markers like:
- "page not found"
- "error 404"
- "the page you requested cannot be found"

If a marker is found, the `soft_404_detected` field in the output is set to `True`, allowing you to filter out these "ghost" pages from your results.

### Trust Tier Classification
To help prioritize analysis, `urlcheck-smith` assigns a trust tier to each URL:
- **TIER_1_OFFICIAL**: Government (`.gov`, `.go.jp`, etc.), UN, and official EU domains.
- **TIER_2_NEWS**: Major news organizations (Reuters, AP, BBC, etc.).
- **TIER_3_GENERAL**: All other domains.

This is available via the `trust_tier` field in CSV/JSONL outputs.

## Installation (development)

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
```

---

# Commands Overview

---

# 1. `scan` — extract → classify → (optional) HTTP check

### CSV output (default)

```bash
urlcheck-smith scan sample.txt -o urls.csv
```

### JSONL output

```bash
urlcheck-smith scan sample.txt \
  --no-http \
  --format jsonl \
  -o urls.jsonl
```

### Skip HTTP check

```bash
urlcheck-smith scan notes.txt --no-http -o urls_wo_status.csv
```

### Custom rules

```bash
urlcheck-smith scan urls.txt \
  --rules my_rules.yaml \
  -o result.csv
```

### Built-in rule presets

```bash
urlcheck-smith scan urls.txt --preset japan -o out.csv
urlcheck-smith scan urls.txt --preset eu -o out.csv
urlcheck-smith scan urls.txt --preset global -o out.csv
```

---

# 2. `classify-url` — classify a single URL

### Default (JSON)

```bash
urlcheck-smith classify-url https://www.soumu.go.jp/
```

### Explain mode

```bash
urlcheck-smith classify-url https://www.soumu.go.jp/ --explain
```

Output example:

```json
{
  "url": "https://www.soumu.go.jp/",
  "base_url": "www.soumu.go.jp",
  "category": "government",
  "trust_tier": "TIER_1_OFFICIAL",
  "explain": {
    "matched_suffix": ".go.jp",
    "category": "government"
  }
}
```

### Quiet mode (machine-friendly)

```bash
urlcheck-smith classify-url https://www.soumu.go.jp/ --quiet
```

### Presets & custom rules

```bash
urlcheck-smith classify-url https://www.gov.uk/ --preset eu
urlcheck-smith classify-url https://policy.example.com/ --rules org_rules.yaml
```

---

# 3. `classify` — batch classify (no HTTP check)

Input file should contain one URL per line.

### CSV output

```bash
urlcheck-smith classify urls.txt -o classified.csv
```

### JSONL output

```bash
urlcheck-smith classify urls.txt --format jsonl -o out.jsonl
```

### Quiet mode

```bash
urlcheck-smith classify urls.txt --quiet
```

### Explain mode

```bash
urlcheck-smith classify urls.txt --explain -o out.jsonl
```

---

### Rule Precedence & Discrepancies

When multiple rule sources are used, they are prioritized as follows:
1. **User rules** (`--rules`): Rules from these files are checked first. If multiple files are provided, the one specified last has the highest priority.
2. **Base rules** (`--preset` or default): These are checked only if no user rule matches.

The system uses a **First-Match-Wins** strategy. The first rule that matches the URL (by domain, suffix, or regex) determines the category and trust tier.

---

# Rule System

## Custom rule file example (YAML)
Rule files can specify `rules` (a list of matchers) and optional `default_category` / `default_trust_tier`.

```yaml
rules:
  - domain: "special.example.com"
    category: "internal"
    trust_tier: "TIER_1_OFFICIAL"
  - suffix: ".gov.uk"
    category: "government"
    trust_tier: "TIER_1_OFFICIAL"
  - regex: ".*-news\\.com$"
    category: "news"
    trust_tier: "TIER_2_RELIABLE"

default_category: "private"
default_trust_tier: "TIER_3_GENERAL"
```

## Built-in presets

- `--preset japan`
- `--preset eu`
- `--preset global`

Each corresponds to a YAML file under `urlcheck_smith/data/`.

---

# Development

```bash
make install
make test
```

---

# License

MIT
