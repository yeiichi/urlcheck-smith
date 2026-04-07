import importlib
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def update_yaml_module(tmp_path):
    """Reload the module with isolated file paths for each test and restore afterwards."""
    module = importlib.import_module("urlcheck_smith.core.update_yaml")
    
    # Save original values
    orig_yaml = module.YAML_FILE
    orig_deny = module.LOCAL_DENYLIST
    orig_key = module.GOOGLE_API_KEY
    
    module = importlib.reload(module)

    module.YAML_FILE = str(tmp_path / "ucsmith_db.yaml")
    module.LOCAL_DENYLIST = str(tmp_path / "denylist.txt")
    module.GOOGLE_API_KEY = "test-api-key"
    
    yield module
    
    # Restore original values
    module.YAML_FILE = orig_yaml
    module.LOCAL_DENYLIST = orig_deny
    module.GOOGLE_API_KEY = orig_key


def test_load_db_missing_file_returns_default_structure(update_yaml_module):
    """Test that a missing YAML file returns the default DB structure."""
    data = update_yaml_module.load_db()

    assert data == {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }


def test_save_and_load_db_round_trip(update_yaml_module):
    """Test that save_db writes data that load_db can read back."""
    sample = {
        "metadata": {"version": 1},
        "user_defined": [{"name": "example.com", "category": "News"}],
        "global_rules": [],
        "discovered_cache": [],
    }

    update_yaml_module.save_db(sample)
    loaded = update_yaml_module.load_db()

    assert loaded["metadata"] == {"version": 1}
    assert loaded["user_defined"] == [{"name": "example.com", "category": "News"}]


def test_add_user_domain_adds_entry(update_yaml_module, monkeypatch):
    """Test that add_user_domain appends a new domain."""
    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.add_user_domain("example.com", category="News")

    save_mock.assert_called_once()
    assert db["user_defined"] == [{"name": "example.com", "category": "News"}]


def test_add_user_domain_does_not_duplicate(update_yaml_module, monkeypatch):
    """Test that add_user_domain skips duplicates."""
    db = {
        "metadata": {},
        "user_defined": [{"name": "example.com", "category": "News"}],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.add_user_domain("example.com", category="General")

    save_mock.assert_not_called()


def test_remove_user_domain_removes_entry(update_yaml_module, monkeypatch):
    """Test that remove_user_domain removes an existing domain."""
    db = {
        "metadata": {},
        "user_defined": [
            {"name": "example.com", "category": "News"},
            {"name": "other.com", "category": "Tech"},
        ],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.remove_user_domain("example.com")

    save_mock.assert_called_once()
    assert db["user_defined"] == [{"name": "other.com", "category": "Tech"}]


def test_remove_user_domain_missing_entry_does_not_save(update_yaml_module, monkeypatch):
    """Test that remove_user_domain does nothing when the domain is absent."""
    db = {
        "metadata": {},
        "user_defined": [{"name": "other.com", "category": "Tech"}],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.remove_user_domain("example.com")

    save_mock.assert_not_called()


def test_modify_user_category_updates_entry(update_yaml_module, monkeypatch):
    """Test that modify_user_category changes an existing entry."""
    db = {
        "metadata": {},
        "user_defined": [{"name": "example.com", "category": "News"}],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.modify_user_category("example.com", "Science")

    save_mock.assert_called_once()
    assert db["user_defined"][0]["category"] == "Science"


def test_clear_user_domains_empties_list(update_yaml_module, monkeypatch):
    """Test that clear_user_domains wipes the user_defined list."""
    db = {
        "metadata": {},
        "user_defined": [{"name": "example.com", "category": "News"}],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    save_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "save_db", save_mock)

    update_yaml_module.clear_user_domains()

    save_mock.assert_called_once()
    assert db["user_defined"] == []


def test_check_google_fact_check_returns_none_without_api_key(update_yaml_module, monkeypatch):
    """Test that the API helper returns None when no key is configured."""
    monkeypatch.setattr(update_yaml_module, "GOOGLE_API_KEY", None)

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


def test_update_cache_adds_new_entry(update_yaml_module, monkeypatch):
    """Test that _update_cache adds a new discovered_cache record."""
    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "save_db", Mock())
    monkeypatch.setattr(update_yaml_module, "datetime", Mock())
    update_yaml_module.datetime.now.return_value.strftime.return_value = "2026-04-07"

    update_yaml_module._update_cache(db, "example.com", 3, 0.2)

    assert db["discovered_cache"] == [
        {
            "name": "example.com",
            "flags_found": 3,
            "credibility_score": 0.2,
            "last_check": "2026-04-07",
        }
    ]


def test_enrich_domain_user_defined_hit_skips_cache(update_yaml_module, monkeypatch):
    """Test that a user_defined shield hit returns early."""
    db = {
        "metadata": {},
        "user_defined": [{"name": "example.com", "category": "News"}],
        "oecd_arrowlist": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    cache_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "_update_cache", cache_mock)

    assert update_yaml_module.enrich_domain("Example.Com") is None
    cache_mock.assert_not_called()


def test_enrich_domain_oecd_hit_skips_cache(update_yaml_module, monkeypatch):
    """Test that an OECD shield hit returns early."""
    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [{"name": "gov"}],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    cache_mock = Mock()
    monkeypatch.setattr(update_yaml_module, "_update_cache", cache_mock)

    assert update_yaml_module.enrich_domain("example.gov") is None
    cache_mock.assert_not_called()


def test_enrich_domain_denylist_updates_cache(update_yaml_module, monkeypatch, tmp_path):
    """Test that denylisted domains are cached with a high flag count."""
    denylist = tmp_path / "denylist.txt"
    denylist.write_text("bad.example\n", encoding="utf-8")
    update_yaml_module.LOCAL_DENYLIST = str(denylist)

    db = {
        "metadata": {},
        "user_defined": [],
        "global_rules": [],
        "discovered_cache": [],
    }

    monkeypatch.setattr(update_yaml_module, "load_db", lambda: db)
    cache_mock = Mock(return_value="cached")
    monkeypatch.setattr(update_yaml_module, "_update_cache", cache_mock)

    result = update_yaml_module.enrich_domain("bad.example")

    assert result == "cached"
    cache_mock.assert_called_once_with(db, "bad.example", 99, 0.0)


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

    result = update_yaml_module.enrich_domain("example.com")

    assert result == "cached"
    cache_mock.assert_called_once_with(db, "example.com", 2, 0.2)