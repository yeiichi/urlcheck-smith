from pathlib import Path

from urlcheck_smith import extract_urls_from_paths, extract_urls_from_text


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


def test_extract_schemeless_url_is_normalized():
    text = "Visit example.com and also https://EXAMPLE.com/."
    records = extract_urls_from_text(text)
    urls = [r.url for r in records]

    assert "http://example.com" in urls
    assert "https://example.com" in urls
    assert len(urls) == 2


def test_extract_from_paths_deduplicates_across_files(tmp_path: Path) -> None:
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"

    file1.write_text("See https://example.com and example.org", encoding="utf-8")
    file2.write_text(
        "Visit https://example.com and http://example.org/page",
        encoding="utf-8",
    )

    records = extract_urls_from_paths([file1, file2])
    urls = [r.url for r in records]

    assert "https://example.com" in urls
    assert "http://example.org" in urls
    assert "http://example.org/page" in urls
    assert len(urls) == 3