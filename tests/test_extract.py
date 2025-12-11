from urlcheck_smith.extract import extract_urls_from_text


def test_extract_basic():
    text = "See https://example.com and http://example.org/page."
    records = extract_urls_from_text(text)
    urls = [r.url for r in records]
    assert "https://example.com" in urls
    assert "http://example.org/page" in urls


def test_extract_trailing_punctuation():
    text = "URL: https://example.com/path)."
    records = extract_urls_from_text(text)
    urls = [r.url for r in records]
    assert urls == ["https://example.com/path"]
