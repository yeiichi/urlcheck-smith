from __future__ import annotations

import csv
import json
import logging
from argparse import ArgumentParser, Namespace
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any, List
from urllib.parse import urlparse

from . import UrlRecord, SiteClassifier, check_urls, extract_urls_from_paths, stream_extract_from_file
from .core.extract import extract_https_urls, urls_to_csv
from .core.update_yaml import add_user_domain, enrich_domain, remove_user_domain, load_db

logger = logging.getLogger(__name__)

PACKAGE_RESOURCE_DB = "ucsmith_db.yaml"
USER_DB_NAME = "usmith_db.yaml"


def build_parser() -> ArgumentParser:
    """
    Builds and returns an ArgumentParser instance configured for the `urlcheck-smith` tool.

    The tool provides multiple subcommands for extracting, classifying, and checking URLs,
    as well as managing a credibility database for domain classification. Each subcommand
    supports specific flags and parameters to customize its behavior.

    Returns:
        ArgumentParser: A configured ArgumentParser instance for the `urlcheck-smith` tool.

    Subcommands:
        scan:
            Extracts URLs from text files and runs a classification and HTTP check pipeline.

            Arguments:
                paths: A list of input text files to scan.
                output: An optional output file path. If not provided, a timestamped filename
                        is generated.
                format: The output file format (`csv` or `jsonl`). Defaults to `csv`.
                no_http: A flag to skip HTTP status checks, limiting the operation to extraction
                         and classification.
                timeout: A timeout value in seconds for HTTP requests. Defaults to 5.0 seconds.
                user_agent: A custom User-Agent string for HTTP requests.
                rules: One or more optional YAML rules files for classification, which are merged
                       with database rules.
                verbose: A flag to enable verbose logging.

        classify-url:
            Classifies a single URL using domain suffix rules.

            Arguments:
                url: The URL to be classified.
                rules: One or more optional YAML rules files for classification, merged with
                       database rules.
                format: The output format (`json` or `text`). Defaults to `json`.
                explain: A flag to provide an explanation for the classification decision.
                preset: A preset configuration for classification, selecting from predefined
                        options such as `japan`, `eu`, or `global`.
                quiet: A flag to suppress output.
                normalize_domain: A flag to normalize the domain before classification.

        classify:
            Classifies multiple URLs from a file without performing HTTP checks.

            Arguments:
                path: A file containing one URL per line.
                output: An optional output file path.
                rules: One or more optional YAML rules files for classification, merged with
                       database rules.
                format: The output format (`csv` or `jsonl`). Defaults to `csv`.
                explain: A flag to provide explanations for classification decisions.
                quiet: A flag to suppress output.
                normalize_domain: A flag to normalize domains before classification.

        db:
            Manages the UC Smith credibility database (`usmith_db.yaml`).

            Subcommands:
                update:
                    Updates or enriches a domain's data in the database.

                    Arguments:
                        domain: The domain to be updated or enriched (e.g., example.com).

                add:
                    Adds a new trusted domain to the user-defined section of the database.

                    Arguments:
                        domain: The domain to add.
                        category: An optional category for the domain. Defaults to `General`.

                remove:
                    Removes a domain from the user-defined section of the database.

                    Arguments:
                        domain: The domain to remove.

        init:
            Creates a local writable `usmith_db.yaml` database file from the standard baseline.

            Arguments:
                force: A flag to overwrite an existing local database file if one exists.
                target: A target path for the initialized database file. Defaults to
                        `./usmith_db.yaml`.
    """
    parser = ArgumentParser(
        prog="urlcheck-smith",
        description="Battery-included URL extraction / classification / HTTP check pipeline.",
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
        help="Manage the UC Smith credibility database (usmith_db.yaml).",
    )
    db_sub = db_parser.add_subparsers(dest="db_command", required=True)

    db_update = db_sub.add_parser(
        "update",
        help="Enrich/Update a domain in the database.",
    )
    db_update_group = db_update.add_mutually_exclusive_group(required=False)
    db_update_group.add_argument(
        "domain", nargs="?", help="Domain to enrich (e.g., example.com)."
    )
    db_update_group.add_argument(
        "--file",
        "-f",
        type=Path,
        help="File containing a list of URLs or domains to enrich.",
    )
    db_update.add_argument(
        "--all",
        action="store_true",
        help="Update all domains currently in the discovered cache.",
    )
    db_update.add_argument(
        "--no-api",
        action="store_true",
        help="Disable Google Fact Check API usage even when the API key is available.",
    )

    db_add = db_sub.add_parser("add", help="Add a trusted domain to user_defined.")
    db_add.add_argument("domain", help="Domain to add.")
    db_add.add_argument("--category", default="General", help="Category for the domain.")

    db_remove = db_sub.add_parser("remove", help="Remove a domain from user_defined.")
    db_remove.add_argument("domain", help="Domain to remove.")

    # --- init subcommand ----------------------------------------------------
    init = sub.add_parser(
        "init",
        help="Create a local writable usmith_db.yaml from the packaged baseline.",
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing local database file.",
    )
    init.add_argument(
        "--target",
        type=Path,
        default=Path.cwd() / USER_DB_NAME,
        help="Target path for the initialized database (default: ./usmith_db.yaml).",
    )

    # --- extract-https subcommand -------------------------------------------
    extract_https = sub.add_parser(
        "extract-https",
        help="Interactively extract unique HTTPS URLs from a file and save them to CSV.",
    )
    extract_https.add_argument(
        "--input",
        "-i",
        type=Path,
        default=None,
        help="Source text file. If omitted, you will be prompted.",
    )
    extract_https.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output CSV path. If omitted, you will be prompted (blank uses a timestamped default).",
    )

    return parser


def _timestamped_output(prefix: str, suffix: str) -> Path:
    """
    Generates a timestamped filepath with the given prefix and suffix.

    The function appends the current timestamp, formatted as "YYYYMMDD_HHMMSS",
    between the provided prefix and suffix to create a unique output filename.

    Args:
        prefix (str): The prefix for the output filename.
        suffix (str): The suffix for the output filename.

    Returns:
        Path: A `Path` object representing the generated timestamped filepath.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"{prefix}_{stamp}{suffix}")


def _init_local_db(target: Path, force: bool = False) -> int:
    """
    Initializes a local database at the specified target location.

    This function creates a local database file at the provided target path. If the file
    already exists and the `force` flag is not set to True, it will not overwrite the
    existing file and will return a success code indicating the database already exists.

    Args:
        target (Path): The path to the target location where the local database is to be
            initialized.
        force (bool): A flag indicating whether to overwrite the database file if it
            already exists. Defaults to False.

    Returns:
        int: A success code indicating the result of the initialization process. Returns
            1 if the database already exists and was not overwritten. Returns 0 if the
            database was successfully initialized.
    """
    if target.exists() and not force:
        logger.warning(f"Database already exists: {target}")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)

    resource_db = resources.files("urlcheck_smith.resources").joinpath(PACKAGE_RESOURCE_DB)
    target.write_text(resource_db.read_text(encoding="utf-8"), encoding="utf-8")

    logger.info(f"Initialized local database at {target}")
    return 0


def run_check(args: Namespace) -> int:
    """
    Extracts URLs from provided paths, classifies the URLs, optionally performs HTTP checks, and writes the
    results to an output file in the specified format.

    Args:
        args (Namespace): The arguments necessary for the URL check process. Expected attributes include:
            - paths (List[str]): A list of paths from which URLs will be extracted.
            - rules (str): Path to the classification rules file.
            - verbose (bool): If True, enables verbose output during URL classification.
            - no_http (bool): If True, skips HTTP checks on the URLs.
            - timeout (int): Timeout in seconds for HTTP requests during the check.
            - user_agent (str): User-Agent string to use for HTTP requests.
            - output (Optional[str]): Optional custom path for the output results. If not provided, a
              timestamped file will be generated.
            - format (str): Format of the output file (e.g., "csv" or "jsonl").

    Returns:
        int: An exit code indicating the success (0) or failure of the process.
    """
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
    Classifies a given URL based on specified rules and outputs the result in either JSON or plain text format.

    This function utilizes the `SiteClassifier` class to apply classification rules and outputs the classification
    result, including details such as category and trust tier. The output format can be controlled via the `args.format`
    parameter.

    Args:
        args (Namespace): The command-line arguments containing the URL to classify and additional classification options,
            such as the path to rules, domain normalization, explanation flag, and output format.

    Returns:
        int: Exit code indicating the status of the execution. Typically, 0 indicates successful classification.
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
        if rec.explain:
            obj["explain"] = rec.explain
        print(json.dumps(obj, ensure_ascii=False))
    else:
        print(f"url={rec.url}")
        print(f"base_url={rec.base_url}")
        print(f"category={rec.category}")
        print(f"trust_tier={rec.trust_tier}")
        if rec.explain:
            print(f"explain={rec.explain}")

    return 0


def run_classify(args: Namespace) -> int:
    """
    Classifies URLs from the input path based on the provided rules and writes the
    classification results to the specified output file. Supports classification in
    multiple output formats (CSV, JSONL).

    Args:
        args (Namespace): The arguments for configuring the classification process.
            Includes the following attributes:
              - path (str): The file path containing URLs to classify.
              - rules (str): The path to the rules for classification.
              - explain (bool): Whether to produce explanation for classifications.
              - normalize_domain (bool): Whether to normalize domain names while classifying.
              - quiet (bool): If True, only prints categories to stdout without saving results.
              - output (str | None): The output file path. If None, creates a timestamped file.
              - format (str): Output format of the classification results, either "csv"
                             or "jsonl".

    Returns:
        int: The exit code of the classification process. Always returns 0 on success.
    """
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
    """
    Executes database-related operations such as updating, adding, or removing domains.

    This function processes commands based on the value of the `db_command` parameter in the
    provided arguments. Supported commands include updating domains with enrichment from 
    a file or domain input, adding user domains with categories, and removing user domains.

    Args:
        args (Namespace): A namespace object containing command arguments for database 
            operations. Expected attributes include `db_command` (str), `file` (Path or None), 
            `domain` (str or None), `category` (str or None), and `no_api` (bool).

    Returns:
        int: An integer indicating the exit status of the operation. Typically, `0` is returned 
            for success, while `1` indicates a failure, such as a missing file.
    """
    args_dict = vars(args)

    if args.db_command == "update":
        use_api = not args_dict.get("no_api", False)
        if args_dict.get("all", False):
            db = load_db()
            cache = db.get("discovered_cache", [])
            if not cache:
                logger.info("No domains in discovered cache to update.")
                return 0
            logger.info(f"Updating all {len(cache)} domains in cache...")
            for entry in cache:
                domain = entry.get("name")
                if domain:
                    logger.info(f"Enriching domain: {domain}")
                    enrich_domain(domain, use_api=use_api)
        elif args_dict.get("file") is not None:
            db_file = args.file
            if not db_file.exists():
                logger.error(f"File not found: {db_file}")
                return 1
            logger.info(f"Bulk enriching domains from {db_file}...")
            domains_seen = set()
            for record in stream_extract_from_file(db_file):
                try:
                    parsed = urlparse(record.url)
                    domain = parsed.netloc or record.url
                    domain = domain.lower().strip()
                    if domain and domain not in domains_seen:
                        logger.info(f"Enriching domain: {domain}")
                        enrich_domain(domain, use_api=use_api)
                        domains_seen.add(domain)
                except Exception as e:
                    logger.error(f"Error processing {record.url}: {e}")
        elif args_dict.get("domain"):
            logger.info(f"Enriching domain: {args.domain}")
            enrich_domain(args.domain, use_api=use_api)
        else:
            logger.error("Please specify a domain, a --file, or use --all.")
            return 1
    elif args.db_command == "add":
        logger.info(f"Adding user domain: {args.domain} ({args.category})")
        add_user_domain(args.domain, args.category)
    elif args.db_command == "remove":
        logger.info(f"Removing user domain: {args.domain}")
        remove_user_domain(args.domain)
    return 0


def run_init(args: Namespace) -> int:
    """
    Initializes the local database with the specified target and options.

    Args:
        args (Namespace): A Namespace object containing the initialization
            parameters. Must include:
                - target (str): The target path or name for the local database
                  initialization.
                - force (bool): A flag indicating whether to force overwrite
                  any existing database.

    Returns:
        int: Status code where 0 indicates success and non-zero indicates failure.
    """
    return _init_local_db(args.target, force=args.force)


def run_extract_https(args: Namespace) -> int:
    """
    Extracts and processes HTTPS URLs from a given source file and writes them to a CSV file.

    This function performs several tasks:
    1. Validates the provided input file path or prompts the user to input it.
    2. Checks the existence and type of the input path to ensure it is a file.
    3. Extracts unique HTTPS URLs from the input file.
    4. Prompts for an output path or uses a timestamped default if not provided.
    5. Writes the extracted URLs to a specified CSV file.
    6. Logs the process at various steps.

    Args:
        args (Namespace): The namespace object containing the following attributes:
            - input (Optional[Path]): The path to the source file containing URLs.
            - output (Optional[Path]): The path to the output CSV file for saving extracted URLs.

    Returns:
        int: Status code. Returns 0 if the operation is successful, 1 otherwise.
    """
    input_path = args.input
    if input_path is None:
        raw = input("Source file path: ").strip()
        if not raw:
            logger.error("No input path provided.")
            return 1
        input_path = Path(raw)

    input_path = input_path.expanduser()
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return 1
    if not input_path.is_file():
        logger.error(f"Not a file: {input_path}")
        return 1

    output_path = args.output
    if output_path is None:
        default = _timestamped_output("https_urls", ".csv")
        raw = input(f"Output CSV path (blank for {default}): ").strip()
        output_path = Path(raw) if raw else default

    output_path = output_path.expanduser()
    urls = extract_https_urls(input_path)
    logger.info(f"Found {len(urls)} unique HTTPS URL(s).")

    logger.info(f"Writing CSV to {output_path}...")
    urls_to_csv(urls, output_path)
    logger.info("Done.")
    return 0


def _record_to_dict(r: UrlRecord) -> dict[str, Any]:
    """
    Converts a UrlRecord object into a dictionary representation.

    This function takes a UrlRecord instance and extracts its relevant
    attributes, converting them into a dictionary format for further use or
    serialization. Attributes with default values or optional fields are
    handled appropriately to ensure a consistent structure in the resulting
    dictionary.

    Args:
        r (UrlRecord): The UrlRecord object to be converted into a dictionary.

    Returns:
        dict[str, Any]: A dictionary containing the extracted attributes from
        the UrlRecord object.
    """
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
    """
    Writes a list of URL records to a CSV file with specified field names.

    This function creates the parent directory of the given file path if it
    does not already exist, then writes the list of `UrlRecord` instances
    into a CSV file. The CSV file includes predefined field names, and any
    missing `http_status` values are replaced with empty strings before
    writing to the file.

    Args:
        path (Path): The file path where the CSV file will be written.
        records (List[UrlRecord]): A list of URL records to be written to the CSV file.

    """
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
    Writes a list of UrlRecord objects to a file in JSONL (JSON Lines) format.

    This function ensures that the directory structure for the specified file path
    exists by creating any missing directories. Each UrlRecord object is converted
    to a dictionary and written as a single line of JSON in the specified file.

    Args:
        path (Path): The file path where the JSONL data will be written.
        records (List[UrlRecord]): A list of UrlRecord objects to serialize into
            JSONL format.

    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for r in records:
            obj = _record_to_dict(r)
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    """
    Executes the main logic of the program. Parses command-line arguments, configures
    logging behavior based on verbosity, and dispatches the requested subcommand
    execution.

    Args:
        argv (list[str] | None): A list of command-line arguments passed to the
            script. If None, sys.argv is used.

    Returns:
        int: The exit code of the program. Generally, 0 indicates successful
            execution and non-zero values indicate an error state.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    if args.command == "scan":
        return run_check(args)
    if args.command == "classify-url":
        return run_classify_url(args)
    if args.command == "classify":
        return run_classify(args)
    if args.command == "db":
        return run_db(args)
    if args.command == "init":
        return run_init(args)
    if args.command == "extract-https":
        return run_extract_https(args)

    parser.print_help()
    return 1


def extract_https_cli() -> int:
    """
    Console-script entry point for extracting HTTPS URLs.

    This keeps argument parsing and logging behavior consistent with the
    `extract-https` subcommand implemented in `main()`.
    """
    import sys

    return main(["extract-https", *sys.argv[1:]])
