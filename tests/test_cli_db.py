from __future__ import annotations

from unittest.mock import Mock

import urlcheck_smith.cli as cli


def test_run_db_update_passes_use_api_true_by_default(monkeypatch):
    enrich_mock = Mock(return_value=None)
    monkeypatch.setattr(cli, "enrich_domain", enrich_mock)

    args = Mock(db_command="update", domain="example.com", no_api=False)

    rc = cli.run_db(args)

    assert rc == 0
    enrich_mock.assert_called_once_with("example.com", use_api=True)


def test_run_db_update_passes_use_api_false_when_disabled(monkeypatch):
    enrich_mock = Mock(return_value=None)
    monkeypatch.setattr(cli, "enrich_domain", enrich_mock)

    args = Mock(db_command="update", domain="example.com", no_api=True)

    rc = cli.run_db(args)

    assert rc == 0
    enrich_mock.assert_called_once_with("example.com", use_api=False)


def test_build_parser_db_update_accepts_no_api_flag():
    parser = cli.build_parser()
    args = parser.parse_args(["db", "update", "example.com", "--no-api"])

    assert args.command == "db"
    assert args.db_command == "update"
    assert args.domain == "example.com"
    assert args.no_api is True