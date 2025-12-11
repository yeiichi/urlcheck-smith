from __future__ import annotations

import json

from urlcheck_smith.cli import main


def test_classify_url_json_default(capsys) -> None:
    argv = ["classify-url", "https://www.soumu.go.jp/"]
    rc = main(argv)
    assert rc == 0

    captured = capsys.readouterr()
    out = captured.out.strip()
    assert out  # non-empty

    data = json.loads(out)
    assert data["url"] == "https://www.soumu.go.jp/"
    assert data["base_url"] == "www.soumu.go.jp"
    # From built-in rules: .go.jp → government
    assert data["category"] == "government"
