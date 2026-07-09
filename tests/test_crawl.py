from __future__ import annotations

from dataclasses import dataclass
from email.message import Message

from urlcheck_smith import crawl_url_layers


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
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
        "https://example.com/d",
        "https://example.com/e",
        "https://example.com/f",
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

    assert crawl_url_layers("https://example.com") == ["https://example.com/ok"]


def test_crawl_url_layers_skips_malformed_url_candidates(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(
            '<a href="http://[bad">bad</a><a href="/ok">OK</a>',
            request.full_url,
        )

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com") == ["https://example.com/ok"]


def test_crawl_url_layers_respects_max_pages(monkeypatch) -> None:
    pages = {
        "https://example.com": '<a href="/a">A</a><a href="/b">B</a>',
        "https://example.com/a": '<a href="/c">C</a>',
    }

    def fake_urlopen(request, timeout):
        url = request.full_url
        return _FakeResponse(pages[url], url)

    monkeypatch.setattr("urlcheck_smith.core.crawl.urlopen", fake_urlopen)

    assert crawl_url_layers("https://example.com", max_pages=2) == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]


def test_crawl_url_layers_defaults_to_depth_1(monkeypatch) -> None:
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
        "https://example.com/a",
        "https://example.com/b",
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

    assert crawl_url_layers("https://example.com", request_interval=0.25) == [
        "https://example.com/a",
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

    assert crawl_url_layers("https://example.com") == ["https://example.com/article"]


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
        "https://example.com/article",
        "https://example.com/app.js",
        "https://example.com/style.css",
        "https://example.com/image.png",
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
        "https://example.com/page",
        "https://example.com/index.html",
        "https://example.com/report.pdf",
        "https://example.com/notes.txt",
        "https://example.com/data.csv",
        "https://example.com/brief.docx",
        "https://example.com/sheet.xlsx",
        "https://example.com/legacy.xlxs",
        "https://example.com/deck.pptx",
    ]
