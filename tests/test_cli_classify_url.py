from __future__ import annotations

import json

from urlcheck_smith.cli import main


def test_classify_url_json_default(capsys) -> None:
    argv = ["classify-url", "https://www.itu.int/en/Pages/default.aspx"]
    rc = main(argv)
    assert rc == 0

    captured = capsys.readouterr()
    out = captured.out.strip()
    assert out  # non-empty

    data = json.loads(out)
    assert data["url"] == "https://www.itu.int/en/Pages/default.aspx"
    assert data["base_url"] == "www.itu.int"
    # From built-in rules: .int → international
    assert data["category"] == "international"
    assert data["trust_tier"] == "TIER_1_OFFICIAL"
