from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .extract import normalize_url

_ABSOLUTE_URL_RE = re.compile(r"https?://[^\s,\"'<>]+", re.IGNORECASE)
_PAGE_URL_ATTRS = {"href", "action"}
_ASSET_URL_ATTRS = {"src", "poster", "data"}
_DEFAULT_TIMEOUT = 5.0
_DEFAULT_MAX_PAGES = 100
_DEFAULT_DEPTH = 1
_DEFAULT_REQUEST_INTERVAL = 0.0
_DEFAULT_USER_AGENT = "UrlCheckSmith/0.8.0"
_HTML_TARGET_EXTENSIONS = {"", ".html", ".htm"}
_DOCUMENT_TARGET_EXTENSIONS = {
    "",
    ".csv",
    ".docx",
    ".htm",
    ".html",
    ".pdf",
    ".pptx",
    ".txt",
    ".xlsx",
    ".xlxs",
}
_STATIC_ASSET_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".mjs",
    ".mp3",
    ".mp4",
    ".ogg",
    ".otf",
    ".png",
    ".svg",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
}


class _HTMLURLParser(HTMLParser):
    def __init__(self, *, include_assets: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.include_assets = include_assets
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect_attrs(attrs)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self._collect_attrs(attrs)

    def handle_data(self, data: str) -> None:
        self.urls.extend(_ABSOLUTE_URL_RE.findall(data))

    def _collect_attrs(self, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is None:
                continue
            attr_name = name.lower()
            if attr_name in _PAGE_URL_ATTRS or (
                self.include_assets and attr_name in _ASSET_URL_ATTRS
            ):
                self.urls.append(value)
            elif self.include_assets and attr_name == "srcset":
                self.urls.extend(_extract_srcset_urls(value))


def _extract_srcset_urls(value: str) -> list[str]:
    urls: list[str] = []
    for candidate in value.split(","):
        candidate_url = candidate.strip().split(maxsplit=1)[0]
        if candidate_url:
            urls.append(candidate_url)
    return urls


def _is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def _is_static_asset_url(url: str) -> bool:
    return any(
        urlparse(url).path.lower().endswith(extension)
        for extension in _STATIC_ASSET_EXTENSIONS
    )


def _url_extension(url: str) -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return f".{name.rsplit('.', 1)[-1].lower()}"


def _is_allowed_target_url(url: str) -> bool:
    return _url_extension(url) in _DOCUMENT_TARGET_EXTENSIONS


def _is_crawlable_html_url(url: str) -> bool:
    return _url_extension(url) in _HTML_TARGET_EXTENSIONS


def _fetch_html(src_uri: str, timeout: float) -> tuple[str, str] | None:
    request = Request(src_uri, headers={"User-Agent": _DEFAULT_USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            if content_type and "html" not in content_type.lower():
                return None

            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            final_url = response.geturl() or src_uri
            return html, final_url
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError):
        return None


def _extract_urls_from_html(
    html: str,
    base_uri: str,
    *,
    include_assets: bool,
) -> list[str]:
    parser = _HTMLURLParser(include_assets=include_assets)
    parser.feed(html)

    urls: list[str] = []
    seen: set[str] = set()
    for raw_url in parser.urls:
        try:
            resolved = urljoin(base_uri, raw_url.strip())
            if not _is_http_url(resolved):
                continue
            normalized = normalize_url(resolved)
            if not include_assets and (
                _is_static_asset_url(normalized)
                or not _is_allowed_target_url(normalized)
            ):
                continue
        except ValueError:
            continue

        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


def crawl_url_layers(
    src_uri: str,
    *,
    max_pages: int = _DEFAULT_MAX_PAGES,
    timeout: float = _DEFAULT_TIMEOUT,
    depth: int = _DEFAULT_DEPTH,
    request_interval: float = _DEFAULT_REQUEST_INTERVAL,
    include_assets: bool = False,
) -> list[str]:
    """
    Crawl a source HTML page to a fixed depth and return discovered URLs.

    The source page is layer 0's input. URLs extracted from that page are layer 0
    results, URLs extracted from layer 0 pages are layer 1 results, and URLs
    extracted from layer 1 pages are layer 2 results. The ``depth`` argument is
    the deepest layer to collect. Fetch failures and non-HTML responses are
    skipped. At most ``max_pages`` pages are fetched, including the source page.
    ``request_interval`` seconds are slept between page fetches. By default,
    output is limited to HTML-like pages plus PDF, TXT, CSV, DOCX, XLSX, and
    PPTX URLs. Static asset URLs and other file types are skipped unless
    ``include_assets`` is true.
    """
    all_urls: list[str] = []
    all_seen: set[str] = set()
    current_inputs = [src_uri]
    fetched_count = 0

    for _layer in range(depth + 1):
        next_inputs: list[str] = []
        next_seen: set[str] = set()

        for uri in current_inputs:
            if fetched_count >= max_pages:
                return all_urls

            if fetched_count > 0 and request_interval > 0:
                time.sleep(request_interval)
            fetched_count += 1
            fetched = _fetch_html(uri, timeout=timeout)
            if fetched is None:
                continue

            html, final_url = fetched
            for url in _extract_urls_from_html(
                html,
                final_url,
                include_assets=include_assets,
            ):
                if url not in all_seen:
                    all_seen.add(url)
                    all_urls.append(url)
                if _is_crawlable_html_url(url) and url not in next_seen:
                    next_seen.add(url)
                    next_inputs.append(url)

        current_inputs = next_inputs

    return all_urls
