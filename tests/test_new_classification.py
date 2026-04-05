from urlcheck_smith import SiteClassifier, UrlRecord

def test_sophisticated_classification():
    classifier = SiteClassifier()
    
    # 1. Government (TIER_1_OFFICIAL)
    recs = [UrlRecord(url="https://www.soumu.go.jp/")]
    out = classifier.classify(recs)
    assert out[0].category == "government"
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

def test_preset_japan_classification():
    classifier = SiteClassifier(preset="japan")
    
    # Nikkei should be news in Japan preset
    recs = [UrlRecord(url="https://www.nikkei.com/")]
    out = classifier.classify(recs)
    assert out[0].category == "news"
    assert out[0].trust_tier == "TIER_2_RELIABLE"

    # Local gov
    recs = [UrlRecord(url="https://www.city.yokohama.lg.jp/")]
    out = classifier.classify(recs)
    assert out[0].category == "local_gov"
    assert out[0].trust_tier == "TIER_1_OFFICIAL"

def test_fallback_patterns():
    classifier = SiteClassifier()
    
    # No explicit YAML rule for nytimes.com in site_categories.yaml, 
    # but it is in NEWS_PATTERNS in trust_manager.py
    recs = [UrlRecord(url="https://www.nytimes.com/")]
    out = classifier.classify(recs)
    assert out[0].trust_tier == "TIER_2_RELIABLE"
    # Category might be default if not in YAML
    assert out[0].category == "private"
