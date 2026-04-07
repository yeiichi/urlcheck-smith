from unittest.mock import Mock, patch

from urlcheck_smith import UrlRecord, check_urls


@patch("urlcheck_smith.core.check.requests.get")
def test_check_success(mock_get: Mock):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/"
    mock_resp.text = "<html><head><title>Example</title></head><body>Hello</body></html>"
    mock_get.return_value = mock_resp

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0)
    assert out[0].http_status == 200
    assert out[0].redirected_url == "https://example.com/"
    assert out[0].error is None


@patch("urlcheck_smith.core.check.requests.get")
@patch("urlcheck_smith.core.check.get_default_user_agent")
def test_check_urls_uses_default_user_agent(mock_default_ua, mock_get: Mock):
    mock_default_ua.return_value = "UrlCheckSmith/0.5.0"

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/"
    mock_resp.text = "<html><body>Hello</body></html>"
    mock_get.return_value = mock_resp

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0)

    assert out[0].http_status == 200
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["headers"]["User-Agent"] == "UrlCheckSmith/0.5.0"


@patch("urlcheck_smith.core.check.requests.get")
def test_check_urls_respects_custom_user_agent(mock_get: Mock):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/"
    mock_resp.text = "<html><body>Hello</body></html>"
    mock_get.return_value = mock_resp

    recs = [UrlRecord(url="https://example.com/")]
    out = check_urls(recs, timeout=1.0, user_agent="CustomUA/1.0")

    assert out[0].http_status == 200
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["headers"]["User-Agent"] == "CustomUA/1.0"
