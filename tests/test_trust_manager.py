# File: tests/test_trust_manager.py

import pytest
from urlcheck_smith import TrustManager


@pytest.fixture
def trust_manager():
    """Fixture to initialize the TrustManager."""
    return TrustManager()


def test_classify_official_url(trust_manager):
    """Test TrustManager identifies a valid official URL (via .gov suffix in DB or OECD)."""
    # Assuming .gov is in oecd_arrowlist in ucsmith_db.yaml
    valid_official_url = "https://example.gov"
    assert trust_manager.classify_url(valid_official_url) == "TIER_1_OFFICIAL"


def test_classify_untrusted_url(trust_manager):
    """Test TrustManager does not identify an invalid URL as official."""
    invalid_url = "https://unofficial.com"
    # Default tier
    assert trust_manager.classify_url(invalid_url) == "TIER_3_GENERAL"


def test_classify_subdomain(trust_manager):
    """Test TrustManager correctly identifies valid subdomain of an official URL."""
    subdomain_url = "https://subdomain.example.gov"
    assert trust_manager.classify_url(subdomain_url) == "TIER_1_OFFICIAL"


def test_audit_list(trust_manager):
    """Test audit_list categorization."""
    urls = [
        "https://example.gov",
        "https://reuters.com",
        "https://unknown.com"
    ]
    report = trust_manager.audit_list(urls)
    assert "https://example.gov" in report["official"]
    assert "https://reuters.com" in report["reliable"]
    assert "https://unknown.com" in report["general"]
