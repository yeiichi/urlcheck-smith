# urlcheck-smith

[![PyPI version](https://img.shields.io/pypi/v/urlcheck-smith.svg)](https://pypi.org/project/urlcheck-smith/)
![Python versions](https://img.shields.io/pypi/pyversions/urlcheck-smith.svg)
![Status](https://img.shields.io/badge/status-Alpha-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

A compact, fast URL analysis pipeline:

- Extract URLs from arbitrary text files  
- Classify domains using suffix-based “site runner” rules (government, edu, private, etc.)  
- Optional HTTP checks (status, redirect, CAPTCHA/human-check heuristic)  
- Output results as CSV or JSONL  
- Standalone URL classifier (`classify-url`)  
- Batch classification mode (`classify`)  
- Supports rule presets (Japan/EU/global), custom YAML rules, explain mode, quiet mode  

---

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

# Rule System

## Custom rule file example

```yaml
suffix_rules:
  - suffix: ".go.jp"
    category: government
  - suffix: ".example.com"
    category: internal

default_category: private
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
