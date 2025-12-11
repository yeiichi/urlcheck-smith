from urlcheck_smith.classify import SiteClassifier
from urlcheck_smith.models import UrlRecord


def test_classify_go_jp():
    recs = [UrlRecord(url="https://www.soumu.go.jp/")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    assert out[0].base_url == "www.soumu.go.jp"
    assert out[0].category == "government"
