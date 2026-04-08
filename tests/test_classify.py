from urlcheck_smith import SiteClassifier, UrlRecord


def test_classify_go_jp():
    recs = [UrlRecord(url="https://www.soumu.go.jp/")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    assert out[0].base_url == "www.soumu.go.jp"
    assert out[0].category == "government"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"
    assert out[0].explain is None


def test_classify_explain():
    recs = [UrlRecord(url="https://www.soumu.go.jp/")]
    classifier = SiteClassifier(explain=True)
    out = classifier.classify(recs)
    assert out[0].category == "government"
    assert out[0].explain is not None
    assert "Matched pattern 'go.jp'" in out[0].explain or "Matched pattern 'soumu.go.jp'" in out[0].explain


def test_classify_default_explain():
    recs = [UrlRecord(url="https://example.unknown/")]
    classifier = SiteClassifier(explain=True)
    out = classifier.classify(recs)
    assert out[0].category == "private"
    assert "No match found" in out[0].explain
