import importlib
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def update_yaml_module(tmp_path):
    """Reload the module with isolated file paths for each test and restore afterwards."""
    module = importlib.import_module("urlcheck_smith.core.update_yaml")
    module = importlib.reload(module)

    module.RESOURCE_DB_NAME = "test_db.yaml"
    module.RESOURCE_DENYLIST_NAME = "test_denylist.txt"
    module.api_key = "test-api-key"

    module._baseline_db_path = lambda: tmp_path / "baseline_db.yaml"
    module._cwd_db_path = lambda: tmp_path / "usmith_db.yaml"

    yield module


def test_check_google_fact_check_returns_none_without_api_key(update_yaml_module, monkeypatch):
    """Test that the API helper returns None when no key is configured."""
    monkeypatch.setattr(update_yaml_module, "api_key", None)

    assert update_yaml_module.check_google_fact_check("example.com") is None


@patch("urlcheck_smith.core.update_yaml.requests.get")
def test_check_google_fact_check_counts_negative_reviews(mock_get, update_yaml_module):
    """Test that negative review labels are counted."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "claims": [
            {"claimReview": [{"textualRating": "False"}]},
            {"claimReview": [{"textualRating": "Mostly false"}]},
            {"claimReview": [{"textualRating": "True"}]},
        ]
    }
    mock_get.return_value = mock_resp

    count = update_yaml_module.check_google_fact_check("example.com")

    assert count == 2


def test_enrich_domain_api_flow_uses_score_and_cache(update_yaml_module, monkeypatch):
    """Test that API results affect the score and cache update."""
    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    monkeypatch.setattr(update_yaml_module, "check_google_fact_check", lambda domain: 2)
    cache_mock = Mock(return_value="cached")
    monkeypatch.setattr(update_yaml_module, "_update_cache", cache_mock)

    result = update_yaml_module.enrich_domain("example.com", use_api=True)

    assert result == "cached"
    cache_mock.assert_called_once_with(db, "example.com", 2, 0.2)


def test_enrich_domain_no_api_skips_fact_check_call(update_yaml_module, monkeypatch):
    """Test that disabling API usage skips the Google Fact Check lookup."""
    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    check_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "check_google_fact_check", check_mock)
    cache_mock = Mock(return_value="cached")
    monkeypatch.setattr(update_yaml_module, "_update_cache", cache_mock)

    result = update_yaml_module.enrich_domain("example.com", use_api=False)

    assert result == "cached"
    check_mock.assert_not_called()
    cache_mock.assert_called_once_with(db, "example.com", 0, 0.5)