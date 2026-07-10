from __future__ import annotations

import csv
from pathlib import Path

import urlcheck_smith.cli as cli
from urlcheck_smith import CrawledURL


def test_build_parser_crawl_accepts_src_uri_and_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "urls.csv"
    parser = cli.build_parser()

    args = parser.parse_args(
        [
            "crawl",
            "https://example.com/start",
            "--output-path",
            str(output_path),
            "--max-pages",
            "20",
            "--depth",
            "2",
            "--timeout",
            "2.5",
            "--request-interval",
            "0.25",
            "--include-assets",
        ]
    )

    assert args.command == "crawl"
    assert args.src_uri == "https://example.com/start"
    assert args.output_path == output_path
    assert args.max_pages == 20
    assert args.depth == 2
    assert args.timeout == 2.5
    assert args.request_interval == 0.25
    assert args.include_assets is True


def test_build_parser_crawl_defaults_depth_to_zero() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["crawl", "https://example.com/start"])

    assert args.depth == 0


def test_run_crawl_writes_csv_with_explicit_output_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_path = tmp_path / "urls.csv"
    monkeypatch.setattr(
        cli,
        "crawl_url_layers",
        lambda src_uri, max_pages, timeout, depth, request_interval, include_assets: [
            CrawledURL("https://example.com/a", "A"),
            CrawledURL("https://example.com/b"),
        ],
    )

    rc = cli.main(
        [
            "crawl",
            "https://example.com/start",
            "--output-path",
            str(output_path),
        ]
    )

    assert rc == 0
    with output_path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["URL", "anchor_text", "hashed_URL"]
    assert [row[:2] for row in rows[1:]] == [
        ["https://example.com/a", "A"],
        ["https://example.com/b", ""],
    ]


def test_run_crawl_reads_src_uri_from_stdin_and_uses_default_output_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "https://example.com/start")
    monkeypatch.setattr(
        cli,
        "crawl_url_layers",
        lambda src_uri, max_pages, timeout, depth, request_interval, include_assets: [
            CrawledURL("https://example.com/a", "A")
        ],
    )

    rc = cli.main(["crawl"])

    assert rc == 0
    output_path = tmp_path / "example.com_start.csv"
    assert output_path.exists()

    with output_path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["URL", "anchor_text", "hashed_URL"]
    assert rows[1][0] == "https://example.com/a"
    assert rows[1][1] == "A"
