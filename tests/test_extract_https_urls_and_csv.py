from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from urlcheck_smith.cli import main
from urlcheck_smith.core.extract import extract_https_urls, urls_to_csv


def test_extract_https_urls_dedup_clean_sort_and_path_str(tmp_path: Path) -> None:
    p = tmp_path / "input.txt"
    p.write_text(
        "\n".join(
            [
                'See https://example.com/path). and also "https://example.com/path" again.',
                "Ignore http://example.org/insecure and keep https://example.org/x,",
                "Also keep https://example.net/zzz] and https://example.org/x",  # dup
            ]
        ),
        encoding="utf-8",
    )

    urls = extract_https_urls(str(p))
    assert urls == [
        "https://example.com/path",
        "https://example.net/zzz",
        "https://example.org/x",
    ]


def test_urls_to_csv_writes_header_and_hashes(tmp_path: Path) -> None:
    out = tmp_path / "urls.csv"
    urls = ["https://example.com", "https://example.org/x"]

    urls_to_csv(urls, out)
    assert out.exists()

    with out.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["URL", "hashed_URL"]
    assert rows[1][0] == urls[0]
    assert rows[2][0] == urls[1]

    assert rows[1][1] == hashlib.sha256(urls[0].encode("utf-8")).hexdigest()
    assert rows[2][1] == hashlib.sha256(urls[1].encode("utf-8")).hexdigest()


def test_cli_extract_https_interactive(tmp_path: Path, monkeypatch) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text(
        "a https://example.com/path) b https://example.org/x, http://example.org/nope",
        encoding="utf-8",
    )
    output_file = tmp_path / "out.csv"

    answers = iter([str(input_file), str(output_file)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    rc = main(["extract-https"])
    assert rc == 0
    assert output_file.exists()

    with output_file.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["URL", "hashed_URL"]
    urls = [r[0] for r in rows[1:]]
    assert urls == ["https://example.com/path", "https://example.org/x"]

