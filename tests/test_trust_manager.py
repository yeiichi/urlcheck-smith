# File: tests/test_trust_manager.py

import pytest
from urlcheck_smith import TrustManager


@pytest.fixture
def trust_manager():
    """Fixture to initialize the TrustManager."""
    return TrustManager()


def test_is_official_valid_url(trust_manager):
    """Test OfficialAuditor identifies a valid official URL."""
    valid_official_url = "https://example.gov"
    assert trust_manager.official_auditor.is_official(valid_official_url) is True


def test_is_official_invalid_url(trust_manager):
    """Test OfficialAuditor does not identify an invalid URL as official."""
    invalid_url = "https://unofficial.com"
    assert trust_manager.official_auditor.is_official(invalid_url) is False


def test_is_official_partial_match(trust_manager):
    """Test OfficialAuditor avoids partial matches in domain."""
    partial_match_url = "https://malicious.com/search?q=.gov"
    assert trust_manager.official_auditor.is_official(partial_match_url) is False


def test_is_official_subdomain(trust_manager):
    """Test OfficialAuditor correctly identifies valid subdomain of an official URL."""
    subdomain_url = "https://subdomain.example.gov"
    assert trust_manager.official_auditor.is_official(subdomain_url) is True


def test_is_official_exception_handling(trust_manager):
    """Test OfficialAuditor handles exceptions gracefully."""
    invalid_format_url = "not_a_url"
    assert trust_manager.official_auditor.is_official(invalid_format_url) is False
