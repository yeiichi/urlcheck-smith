import pytest
from urlcheck_smith import SiteClassifier, UrlRecord

def test_user_defined_rule_matching():
    # un.org is defined as category 'international' in user_defined section of the YAML
    recs = [UrlRecord(url="https://www.un.org/")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    
    # Previously, user_defined was only exact match in _classify_base, 
    # so 'www.un.org' would fail to match 'un.org' unless 'un.org' was also a suffix rule.
    # Now, all user_defined entries are added as suffix rules.
    assert out[0].category == "international"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"

def test_user_defined_subdomain_matching():
    # Test if subdomain of a user_defined entry is also matched
    recs = [UrlRecord(url="https://sub.un.org/path")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    
    assert out[0].category == "international"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"

def test_global_rule_matching():
    # ac.jp is in global_rules
    recs = [UrlRecord(url="https://u-tokyo.ac.jp/")]
    classifier = SiteClassifier()
    out = classifier.classify(recs)
    
    assert out[0].category == "education"
    assert out[0].trust_tier == "TIER_2_RELIABLE"
