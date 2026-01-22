from unittest.mock import MagicMock, patch
from urlcheck_smith.check import check_urls, _is_soft_404
from urlcheck_smith.models import UrlRecord

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

@patch("requests.get")
def test_check_urls_detects_soft_404(mock_get):
    """Test that check_urls flags a 200 OK response containing 404 markers."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/broken"
    mock_resp.text = "<html><body><h1>404 - File Not Found</h1></body></html>"
    mock_get.return_value = mock_resp

    records = [UrlRecord(url="https://example.com/broken")]
    results = check_urls(records)

    assert results[0].soft_404_detected is True

@patch("requests.get")
def test_check_urls_detects_soft_404_japanese(mock_get):
    """Test that check_urls flags a Japanese soft 404 page."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.jp/missing"
    mock_resp.text = "<html><body><h1>404 お探しのページは見つかりませんでした。</h1></body></html>"
    mock_get.return_value = mock_resp

    records = [UrlRecord(url="https://example.jp/missing")]
    results = check_urls(records)

    assert results[0].soft_404_detected is True

@patch("requests.get")
def test_check_urls_normal_page(mock_get):
    """Test that a normal 200 OK page is not flagged."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/ok"
    mock_resp.text = "Welcome to the site!"
    mock_get.return_value = mock_resp

    records = [UrlRecord(url="https://example.com/ok")]
    results = check_urls(records)

    assert results[0].soft_404_detected is False