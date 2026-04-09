from urlcheck_smith import SiteClassifier, UrlRecord

def test_sophisticated_classification():
    classifier = SiteClassifier()
    
    # 1. International (TIER_1_OFFICIAL)
    recs = [UrlRecord(url="https://www.itu.int/en/Pages/default.aspx")]
    out = classifier.classify(recs)
    assert out[0].category == "international"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"
    
    # 2. News (TIER_2_RELIABLE)
    recs = [UrlRecord(url="https://www.reuters.com/news")]
    out = classifier.classify(recs)
    assert out[0].category == "news"
    assert out[0].trust_tier == "TIER_2_RELIABLE"
    
    # 3. Education (TIER_2_RELIABLE)
    recs = [UrlRecord(url="https://www.u-tokyo.ac.jp/")]
    out = classifier.classify(recs)
    assert out[0].category == "education"
    assert out[0].trust_tier == "TIER_2_RELIABLE"
    
    # 4. Global International (TIER_1_OFFICIAL)
    recs = [UrlRecord(url="https://news.un.org/en/")]
    out = classifier.classify(recs)
    assert out[0].category == "international"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"

def test_fallback_patterns():
    classifier = SiteClassifier()
    
    # nytimes.com is now in global_rules of ucsmith_db.yaml
    recs = [UrlRecord(url="https://www.nytimes.com/")]
    out = classifier.classify(recs)
    assert out[0].trust_tier == "TIER_2_RELIABLE"
    assert out[0].category == "news"
