from unittest.mock import Mock, patch

from urlcheck_smith.check import check_urls
from urlcheck_smith.models import UrlRecord


@patch("urlcheck_smith.check.requests.get")
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
