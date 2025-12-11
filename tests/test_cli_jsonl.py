# tests/test_cli_jsonl.py
from __future__ import annotations

import json
from pathlib import Path

from urlcheck_smith.cli import main


def test_scan_jsonl_no_http(tmp_path: Path) -> None:
    # Prepare input file with two URLs
    input_file = tmp_path / "input.txt"
    input_file.write_text(
        "See https://example.com and https://www.soumu.go.jp/ .",
        encoding="utf-8",
    )

    output_file = tmp_path / "out.jsonl"

    # Run CLI (no HTTP to keep the test fast and deterministic)
    argv = [
        "scan",
        str(input_file),
        "--no-http",
        "--format",
        "jsonl",
        "-o",
        str(output_file),
    ]
    rc = main(argv)
    assert rc == 0
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # two unique URLs

    objs = [json.loads(line) for line in lines]
    urls = {obj["url"] for obj in objs}
    assert "https://example.com" in urls
    assert "https://www.soumu.go.jp/" in urls

    # classification is present (category non-empty)
    categories = {obj["category"] for obj in objs}
    assert "" not in categories
