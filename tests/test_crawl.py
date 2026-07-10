from __future__ import annotations

from dataclasses import dataclass
from email.message import Message

from urlcheck_smith import CrawledURL, crawl_url_layers


@dataclass
class _FakeResponse:
    body: str
    url: str
    content_type: str = "text/html; charset=utf-8"

    def __post_init__(self) -> None:
        self.headers = Message()
        self.headers["content-type"] = self.content_type

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")

    def geturl(self) -> str:
        return self.url


def test_crawl_url_layers_returns_layers_0_to_2(monkeypatch) -> None:
    pages = {
        "https://example.com": """
            <a href="/a">A</a>
            <a href="https://example.com/b#section">B</a>
        """,
        "https://example.com/a": '<a href="/c">C</a>',
        "https://example.com/b": '<a href="/d">D</a>',
        "https://example.com/c": '<a href="/e">E</a>',
        "https://example.com/d": '<a href="/f">F</a>',
    }

    def fake_urlopen(request, timeout):
        url = request.full_url
        return _FakeResponse(pages[url], url)

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    urls = crawl_url_layers("https://example.com", depth=2)

    assert urls == [
        CrawledURL("https://example.com/a", "A"),
        CrawledURL("https://example.com/b", "B"),
        CrawledURL("https://example.com/c", "C"),
        CrawledURL("https://example.com/d", "D"),
        CrawledURL("https://example.com/e", "E"),
        CrawledURL("https://example.com/f", "F"),
    ]


def test_crawl_url_layers_skips_non_html(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse("not html", request.full_url, content_type="text/plain")

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == []


def test_crawl_url_layers_accepts_missing_content_type(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse('<a href="/ok">OK</a>', request.full_url, content_type="")

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/ok", "OK")
    ]


def test_crawl_url_layers_skips_malformed_url_candidates(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            '<a href="http://[bad">bad</a><a href="/ok">OK</a>',
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/ok", "OK")
    ]


def test_crawl_url_layers_uses_none_when_anchor_text_is_unavailable(
    monkeypatch,
) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            "See https://example.com/plain for details.",
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/plain", None)
    ]


def test_crawl_url_layers_prefers_available_anchor_text_for_duplicate_url(
    monkeypatch,
) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            """
            <form action="/contact"></form>
            <a href="/contact">Contact <strong>team</strong></a>
            """,
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/contact", "Contact team")
    ]


def test_crawl_url_layers_respects_max_pages(monkeypatch) -> None:
    pages = {
        "https://example.com": '<a href="/a">A</a><a href="/b">B</a>',
        "https://example.com/a": '<a href="/c">C</a>',
    }

    def fake_urlopen(request, timeout):
        url = request.full_url
        return _FakeResponse(pages[url], url)

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com", max_pages=2, depth=1) == [
        CrawledURL("https://example.com/a", "A"),
        CrawledURL("https://example.com/b", "B"),
        CrawledURL("https://example.com/c", "C"),
    ]


def test_crawl_url_layers_defaults_to_depth_0(monkeypatch) -> None:
    pages = {
        "https://example.com": '<a href="/a">A</a>',
        "https://example.com/a": '<a href="/b">B</a>',
        "https://example.com/b": '<a href="/c">C</a>',
    }

    def fake_urlopen(request, timeout):
        url = request.full_url
        return _FakeResponse(pages[url], url)

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/a", "A"),
    ]


def test_crawl_url_layers_waits_between_requests(monkeypatch) -> None:
    pages = {
        "https://example.com": '<a href="/a">A</a>',
        "https://example.com/a": "",
    }
    sleeps = []

    def fake_urlopen(request, timeout):
        url = request.full_url
        return _FakeResponse(pages[url], url)

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)
    monkeypatch.setattr("urlcheck_smith.core.crawl.time.sleep", sleeps.append)

    assert crawl_url_layers("https://example.com", request_interval=0.25, depth=1) == [
        CrawledURL("https://example.com/a", "A"),
    ]
    assert sleeps == [0.25]


def test_crawl_url_layers_skips_static_assets_by_default(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            """
            <a href="/article">Article</a>
            <script src="/app.js"></script>
            <link href="/style.css" rel="stylesheet">
            <img src="/image.png">
            """,
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == [
        CrawledURL("https://example.com/article", "Article")
    ]


def test_crawl_url_layers_can_include_static_assets(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            """
            <a href="/article">Article</a>
            <script src="/app.js"></script>
            <link href="/style.css" rel="stylesheet">
            <img src="/image.png">
            """,
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com", include_assets=True) == [
        CrawledURL("https://example.com/article", "Article"),
        CrawledURL("https://example.com/app.js"),
        CrawledURL("https://example.com/style.css"),
        CrawledURL("https://example.com/image.png"),
    ]


def test_crawl_url_layers_limits_default_targets_to_pages_and_documents(
    monkeypatch,
) -> None:
    def fake_urlopen(request, timeout):
        assert request.full_url == "https://example.com"
        return _FakeResponse(
            """
            <a href="/page">Page</a>
            <a href="/index.html">HTML</a>
            <a href="/report.pdf">PDF</a>
            <a href="/notes.txt">TXT</a>
            <a href="/data.csv">CSV</a>
            <a href="/brief.docx">DOCX</a>
            <a href="/sheet.xlsx">XLSX</a>
            <a href="/legacy.xlxs">XLXS typo</a>
            <a href="/deck.pptx">PPTX</a>
            <a href="/feed.xml">XML</a>
            <a href="/archive.zip">ZIP</a>
            """,
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com", max_pages=1) == [
        CrawledURL("https://example.com/page", "Page"),
        CrawledURL("https://example.com/index.html", "HTML"),
        CrawledURL("https://example.com/report.pdf", "PDF"),
        CrawledURL("https://example.com/notes.txt", "TXT"),
        CrawledURL("https://example.com/data.csv", "CSV"),
        CrawledURL("https://example.com/brief.docx", "DOCX"),
        CrawledURL("https://example.com/sheet.xlsx", "XLSX"),
        CrawledURL("https://example.com/deck.pptx", "PPTX"),
    ]
