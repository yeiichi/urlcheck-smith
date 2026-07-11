from email.message import Message
from unittest.mock import patch

from urlcheck_smith import UrlRecord, check_urls
from urlcheck_smith.core.check import _is_soft_404


class _FakeResponse:
    def __init__(
        self,
        body: str,
        url: str,
        status: int = 200,
        charset: str = "utf-8",
    ) -> None:
        self.status = status
        self._body = body.encode(charset)
        self._url = url
        self.headers = Message()
        self.headers["content-type"] = f"text/html; charset={charset}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self) -> bytes:
        return self._body


def test_is_soft_404_logic():
    """Test the internal helper with various snippets."""
    assert _is_soft_404("This is a Page Not Found error") is True
    assert _is_soft_404("Error 404: something went wrong") is True
    # Test Japanese marker
    assert _is_soft_404("申し訳ありませんが、ページが見つかりません。") is True
    # Test French marker
    assert _is_soft_404("Désolé, page non trouvée") is True
    assert _is_soft_404("Welcome to our homepage!") is False
    assert _is_soft_404("") is False


@patch("urlcheck_smith.core.check.urlopen")
def test_check_urls_detects_soft_404(mock_urlopen):
    """Test that check_urls flags a 200 OK response containing 404 markers."""
    mock_urlopen.return_value = _FakeResponse(
        "<html><body><h1>404 - File Not Found</h1></body></html>",
        "https://example.com/broken",
    )

    records = [UrlRecord(url="https://example.com/broken")]
    results = check_urls(records)

    assert results[0].soft_404_detected is True


@patch("urlcheck_smith.core.check.urlopen")
def test_check_urls_detects_soft_404_japanese(mock_urlopen):
    """Test that check_urls flags a Japanese soft 404 page."""
    mock_urlopen.return_value = _FakeResponse(
        "<html><body><h1>404 お探しのページは見つかりませんでした。</h1></body></html>",
        "https://example.jp/missing",
    )

    records = [UrlRecord(url="https://example.jp/missing")]
    results = check_urls(records)

    assert results[0].soft_404_detected is True


@patch("urlcheck_smith.core.check.urlopen")
def test_check_urls_normal_page(mock_urlopen):
    """Test that a normal 200 OK page is not flagged."""
    mock_urlopen.return_value = _FakeResponse(
        "Welcome to the site!",
        "https://example.com/ok",
    )

    records = [UrlRecord(url="https://example.com/ok")]
    results = check_urls(records)

    assert results[0].soft_404_detected is False
