from urlcheck_smith import SiteClassifier, UrlRecord


def test_classify_itu():
    recs = [UrlRecord(url="https://www.itu.int/en/Pages/default.aspx")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    assert out[0].base_url == "www.itu.int"
    assert out[0].category == "international"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"
    assert out[0].explain is None


def test_classify_explain():
    recs = [UrlRecord(url="https://www.itu.int/en/Pages/default.aspx")]
    classifier = SiteClassifier(explain=True)
    out = classifier.classify(recs)
    assert out[0].category == "international"
    assert out[0].explain is not None
    assert "Matched pattern 'int'" in out[0].explain


def test_classify_default_explain():
    recs = [UrlRecord(url="https://example.unknown/")]
    classifier = SiteClassifier(explain=True)
    out = classifier.classify(recs)
    assert out[0].category == "private"
    assert "No match found" in out[0].explain
