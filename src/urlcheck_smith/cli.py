from __future__ import annotations

import csv
import json
import logging
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import Any, List

from . import UrlRecord, SiteClassifier, check_urls, extract_urls_from_paths
from .core.update_yaml import add_user_domain, enrich_domain, remove_user_domain

logger = logging.getLogger(__name__)


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
        default=None,
        help="Output file. If omitted, a timestamped filename is generated.",
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
        action="append",
        help="Optional YAML rules file for classifier (merges with database rules). Can be specified multiple times.",
    )
    scan.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging."
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
        action="append",
        help="Optional YAML rules file for classifier (merges with database rules). Can be specified multiple times.",
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
    batch.add_argument("-o", "--output", type=Path, default=None)
    batch.add_argument(
        "--rules",
        type=Path,
        action="append",
        help="Custom YAML rules. Merges with database rules. Can be specified multiple times.",
    )
    batch.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    batch.add_argument("--explain", action="store_true")
    batch.add_argument("--quiet", action="store_true")
    batch.add_argument("--normalize-domain", action="store_true")

    # --- db subcommand ------------------------------------------------------
    db_parser = sub.add_parser(
        "db",
        help="Manage the UC Smith credibility database (ucsmith_db.yaml).",
    )
    db_sub = db_parser.add_subparsers(dest="db_command", required=True)

    # db update
    db_update = db_sub.add_parser("update", help="Enrich/Update a domain in the database.")
    db_update.add_argument("domain", help="Domain to enrich (e.g., example.com).")

    # db add
    db_add = db_sub.add_parser("add", help="Add a trusted domain to user_defined.")
    db_add.add_argument("domain", help="Domain to add.")
    db_add.add_argument("--category", default="General", help="Category for the domain.")

    # db remove
    db_remove = db_sub.add_parser("remove", help="Remove a domain from user_defined.")
    db_remove.add_argument("domain", help="Domain to remove.")

    return parser


def _timestamped_output(prefix: str, suffix: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"{prefix}_{stamp}{suffix}")


def run_scan(args: Namespace) -> int:
    paths = [Path(p) for p in args.paths]
    logger.info(f"Extracting URLs from {len(paths)} path(s)...")
    records: List[UrlRecord] = extract_urls_from_paths(paths)
    logger.info(f"Found {len(records)} unique URLs.")

    logger.info("Classifying URLs...")
    classifier = SiteClassifier(
        rules_path=args.rules,
        explain=args.verbose,
    )
    records = classifier.classify(records)

    if not args.no_http:
        logger.info(f"Running HTTP checks (timeout={args.timeout}s)...")
        records = check_urls(
            records,
            timeout=args.timeout,
            user_agent=args.user_agent,
        )

    output = args.output
    if output is None:
        output = _timestamped_output(
            "urlcheck_results",
            ".csv" if args.format == "csv" else ".jsonl",
        )

    logger.info(f"Writing results to {output}...")
    if args.format == "csv":
        write_csv(output, records)
    else:
        write_jsonl(output, records)

    logger.info("Done.")
    return 0


def run_classify_url(args: Namespace) -> int:
    """
    Classify a single URL and print the result to stdout.
    """
    classifier = SiteClassifier(
        rules_path=args.rules,
        explain=args.explain,
        normalize_domain=args.normalize_domain,
    )
    rec = UrlRecord(url=args.url)
    rec = classifier.classify([rec])[0]

    if args.format == "json":
        obj = {
            "url": rec.url,
            "base_url": rec.base_url,
            "category": rec.category,
            "trust_tier": rec.trust_tier,
        }
        print(json.dumps(obj, ensure_ascii=False))
    else:
        print(f"url={rec.url}")
        print(f"base_url={rec.base_url}")
        print(f"category={rec.category}")
        print(f"trust_tier={rec.trust_tier}")

    return 0


def run_classify(args: Namespace) -> int:
    logger.info(f"Reading URLs from {args.path}...")
    recs = extract_urls_from_paths([args.path])
    logger.info(f"Loaded {len(recs)} URLs.")

    logger.info("Classifying...")
    clf = SiteClassifier(
        rules_path=args.rules,
        explain=args.explain,
        normalize_domain=args.normalize_domain,
    )
    recs = clf.classify(recs)

    if args.quiet:
        for r in recs:
            print(r.category)
        return 0

    output = args.output
    if output is None:
        output = _timestamped_output(
            "classified",
            ".csv" if args.format == "csv" else ".jsonl",
        )

    logger.info(f"Writing results to {output}...")
    if args.format == "csv":
        write_csv(output, recs)
    else:
        write_jsonl(output, recs)

    logger.info("Done.")
    return 0


def run_db(args: Namespace) -> int:
    if args.db_command == "update":
        logger.info(f"Enriching domain: {args.domain}")
        enrich_domain(args.domain)
    elif args.db_command == "add":
        logger.info(f"Adding user domain: {args.domain} ({args.category})")
        add_user_domain(args.domain, args.category)
    elif args.db_command == "remove":
        logger.info(f"Removing user domain: {args.domain}")
        remove_user_domain(args.domain)
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
        "trust_tier": r.trust_tier or "TIER_3_GENERAL",
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
        "trust_tier",
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

    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    if args.command == "scan":
        return run_scan(args)
    if args.command == "classify-url":
        return run_classify_url(args)
    if args.command == "classify":
        return run_classify(args)
    if args.command == "db":
        return run_db(args)

    parser.print_help()
    return 1