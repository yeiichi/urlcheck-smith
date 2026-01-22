from __future__ import annotations

import csv
import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Any

from .check import check_urls
from .classify import SiteClassifier
from .extract import extract_urls_from_paths
from .models import UrlRecord


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="urlcheck-smith",
        description="Minimal URL extraction / classification / HTTP check pipeline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- scan subcommand -----------------------------------------------------
    scan = sub.add_parser(
        "scan",
        help="Extract URLs from text files and run classify+check pipeline.",
    )
    scan.add_argument(
        "paths",
        nargs="+",
        help="Input files to scan (treated as plain text).",
    )
    scan.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("urlcheck_results.csv"),
        help="Output file (default: urlcheck_results.csv)",
    )
    scan.add_argument(
        "--format",
        choices=["csv", "jsonl"],
        default="csv",
        help="Output format: csv (default) or jsonl.",
    )
    scan.add_argument(
        "--no-http",
        action="store_true",
        help="Skip HTTP status check (extract+classify only).",
    )
    scan.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout per request in seconds (default: 5.0).",
    )
    scan.add_argument(
        "--user-agent",
        help="Custom User-Agent for HTTP requests.",
    )
    scan.add_argument(
        "--rules",
        type=Path,
        help="Optional YAML rules file for classifier (overrides built-in rules).",
    )

    # --- classify-url subcommand --------------------------------------------
    classify = sub.add_parser(
        "classify-url",
        help="Classify a single URL using suffix rules.",
    )
    classify.add_argument(
        "url",
        help="URL to classify.",
    )
    classify.add_argument(
        "--rules",
        type=Path,
        help="Optional YAML rules file for classifier (overrides built-in rules).",
    )
    classify.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: json (default) or text.",
    )

    classify.add_argument("--explain", action="store_true")
    classify.add_argument("--preset", choices=["japan", "eu", "global"])
    classify.add_argument("--quiet", action="store_true")
    classify.add_argument("--normalize-domain", action="store_true")

    # classify (batch)
    batch = sub.add_parser(
        "classify",
        help="Classify URLs from a file (one URL per line). No HTTP check.",
    )
    batch.add_argument("path", type=Path, help="File with one URL per line.")
    batch.add_argument("-o", "--output", type=Path, default=Path("classified.csv"))
    batch.add_argument("--rules", type=Path, help="Custom YAML rules.")
    batch.add_argument("--preset", choices=["japan", "eu", "global"])
    batch.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    batch.add_argument("--explain", action="store_true")
    batch.add_argument("--quiet", action="store_true")
    batch.add_argument("--normalize-domain", action="store_true")

    return parser


def run_scan(args: Namespace) -> int:
    paths = [Path(p) for p in args.paths]
    records: List[UrlRecord] = extract_urls_from_paths(paths)

    classifier = SiteClassifier(rules_path=args.rules)
    records = classifier.classify(records)

    if not args.no_http:
        records = check_urls(
            records,
            timeout=args.timeout,
            user_agent=args.user_agent,
        )

    if args.format == "csv":
        write_csv(args.output, records)
    else:
        write_jsonl(args.output, records)

    return 0


def run_classify_url(args: Namespace) -> int:
    """
    Classify a single URL and print the result to stdout.
    """
    classifier = SiteClassifier(rules_path=args.rules)
    rec = UrlRecord(url=args.url)
    rec = classifier.classify([rec])[0]

    if args.format == "json":
        obj = {
            "url": rec.url,
            "base_url": rec.base_url,
            "category": rec.category,
        }
        print(json.dumps(obj, ensure_ascii=False))
    else:
        print(f"url={rec.url}")
        print(f"base_url={rec.base_url}")
        print(f"category={rec.category}")

    return 0


def run_classify(args: Namespace) -> int:
    urls = [
        line.strip()
        for line in args.path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    recs = [UrlRecord(url=u) for u in urls]

    clf = SiteClassifier(
        rules_path=args.rules,
        preset=args.preset,
        explain=args.explain,
        normalize_domain=args.normalize_domain,
    )
    recs = clf.classify(recs)

    if args.quiet:
        for r in recs:
            print(r.category)
        return 0

    if args.format == "csv":
        write_csv(args.output, recs)
    else:
        write_jsonl(args.output, recs)

    return 0


def _record_to_dict(r: UrlRecord) -> dict[str, Any]:
    d: dict[str, Any] = {
        "url": r.url,
        "base_url": r.base_url or "",
        "category": r.category or "",
        "http_status": r.http_status if r.http_status is not None else None,
        "redirected_url": r.redirected_url or "",
        "error": r.error or "",
        "human_check_suspected": bool(r.human_check_suspected),
        "soft_404_detected": bool(r.soft_404_detected),
    }
    if getattr(r, "explain", None):
        d["explain"] = r.explain
    return d


def write_csv(path: Path, records: List[UrlRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "url",
        "base_url",
        "category",
        "http_status",
        "redirected_url",
        "error",
        "human_check_suspected",
        "soft_404_detected",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = _record_to_dict(r)
            if row["http_status"] is None:
                row["http_status"] = ""
            writer.writerow(row)


def write_jsonl(path: Path, records: List[UrlRecord]) -> None:
    """
    Write line-delimited JSON (JSONL), one record per line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for r in records:
            obj = _record_to_dict(r)
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return run_scan(args)
    if args.command == "classify-url":
        return run_classify_url(args)
    if args.command == "classify":
        return run_classify(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
