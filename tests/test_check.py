from email.message import Message
from unittest.mock import Mock, patch

from urlcheck_smith import UrlRecord, check_urls


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


@patch("urlcheck_smith.core.check.urlopen")
def test_check_success(mock_urlopen: Mock):
    mock_urlopen.return_value = _FakeResponse(
        "<html><head><title>Example</title></head><body>Hello</body></html>",
        "https://example.com/",
    )

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0)
    assert out[0].http_status == 200
    assert out[0].redirected_url == "https://example.com/"
    assert out[0].error is None


@patch("urlcheck_smith.core.check.urlopen")
@patch("urlcheck_smith.core.check.get_default_user_agent")
def test_check_urls_uses_default_user_agent(mock_default_ua, mock_urlopen: Mock):
    mock_default_ua.return_value = "UrlCheckSmith/0.5.0"

    mock_urlopen.return_value = _FakeResponse(
        "<html><body>Hello</body></html>",
        "https://example.com/",
    )

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0)

    assert out[0].http_status == 200
    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args.args[0]
    assert request.headers["User-agent"] == "UrlCheckSmith/0.5.0"


@patch("urlcheck_smith.core.check.urlopen")
def test_check_urls_respects_custom_user_agent(mock_urlopen: Mock):
    mock_urlopen.return_value = _FakeResponse(
        "<html><body>Hello</body></html>",
        "https://example.com/",
    )

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0, user_agent="CustomUA/1.0")

    assert out[0].http_status == 200
    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args.args[0]
    assert request.headers["User-agent"] == "CustomUA/1.0"
