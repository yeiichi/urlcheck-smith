# urlcheck-smith

[![GitHub](https://img.shields.io/badge/GitHub-yeiichi%2Furlcheck--smith-181717?logo=github)](https://github.com/yeiichi/urlcheck-smith)
[![PyPI version](https://img.shields.io/pypi/v/urlcheck-smith.svg)](https://pypi.org/project/urlcheck-smith/)
![Python versions](https://img.shields.io/pypi/pyversions/urlcheck-smith.svg)
![Status](https://img.shields.io/badge/status-Alpha-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
[![Documentation Status](https://readthedocs.org/projects/urlcheck-smith/badge/?version=latest)](https://urlcheck-smith.readthedocs.io/en/latest/?badge=latest)

A compact, fast URL analysis pipeline:

- Extract URLs from arbitrary text files  
- Classify domains using suffix-based “site runner” rules (government, edu, private, etc.)
- Trust Tier classification (Official, News, General)
- Optional HTTP checks (status, redirect, CAPTCHA/human-check heuristic)
- Output results as CSV or JSONL
- Standalone URL classifier (`classify-url`)
- Batch classification mode (`classify`)
- Database management command (`db`) to enrich or add custom trusted domains
- Supports custom YAML rules, explain mode, quiet mode
- **Classification**: Assigns categories (e.g., government, education) based on domain suffix rules from the built-in UC Smith database.
- **HTTP Verification**: Checks reachability and captures status codes.
- **Soft 404 Detection**: Identifies pages that return a `200 OK` status but contain "Page Not Found" text.
- **Trust Tier Analysis**: Automatically categorizes URLs into `TIER_1_OFFICIAL`, `TIER_2_RELIABLE`, or `TIER_3_GENERAL` using `TrustManager`.
- **Human-Check Detection**: Flags URLs that likely lead to CAPTCHA or bot-detection screens.
- **Enrichment**: Query the Google Fact Check API to scout for known misinformation flags and update the credibility score.

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
- **TIER_1_OFFICIAL**: Government (`.gov`, `.go.jp`, etc.), UN, and official international domains.
- **TIER_2_RELIABLE**: Verified news organizations (Reuters, AP, BBC, etc.) and educational institutions.
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

### Built-in rules
The system comes with a built-in database (`ucsmith_db.yaml`) containing thousands of government, educational, and news domains. These are used automatically.

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

### Custom rules
```bash
urlcheck-smith classify-url https://policy.example.com/ --rules org_rules.yaml
```

---

# 3. `classify` — batch classify (no HTTP check)

Extracts and classifies URLs from input files.

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

### Rule Precedence
When multiple rule sources are used, they are prioritized as follows:
1. **User defined** in database (`db add` command)
2. **User rules files** (`--rules` flag)
3. **Global rules** in database (`ucsmith_db.yaml`)

The system uses a **Longest-Suffix-Match** strategy. More specific rules (e.g., `blog.google.com`) will match before more general ones (e.g., `google.com`).

---

## API Key (Optional)

A Google API key is **only required** for domain enrichment via the `db update` command. All core features (scanning, classification, HTTP checks) work without it.

This package reads the API key from:

    UCSMITH_GOOGLE_API_KEY

Set it as follows:

    export UCSMITH_GOOGLE_API_KEY="your-api-key"

If your key is stored under another variable name, map it:

    export UCSMITH_GOOGLE_API_KEY="$YOUR_EXISTING_VAR"

- **Service**: Google Fact Check Tools API
- **Usage**: Used to scout for known misinformation flags to update domain credibility scores.

---

---

# 4. `db` — manage the UC Smith database

Manage your local credibility database (`ucsmith_db.yaml`).

### Add a trusted domain
```bash
urlcheck-smith db add my-org.com --category organization
```

### Remove a domain
```bash
urlcheck-smith db remove my-org.com
```

### Enrich a domain via Google Fact Check API
Scouts for known misinformation flags and updates the credibility score in the local cache. Requires `UCSMITH_GOOGLE_API_KEY` (Google Fact Check Tools API key) to be set in the environment.
```bash
export UCSMITH_GOOGLE_API_KEY="your-api-key"
urlcheck-smith db update example.com
```

---

# Rule System

## Custom rule file example (YAML)
Rule files can specify `rules` (a list of matchers) and optional `default_category` / `default_trust_tier`. Note: The internal database uses a simplified `name` field for both domains and suffixes.

```yaml
rules:
  - domain: "special.example.com"
    category: "internal"
    trust_tier: "TIER_1_OFFICIAL"
  - suffix: "gov.uk"
    category: "government"
    trust_tier: "TIER_1_OFFICIAL"

default_category: "private"
default_trust_tier: "TIER_3_GENERAL"
```

---

# Development

```bash
make install
make test
```

---

# License

MIT
