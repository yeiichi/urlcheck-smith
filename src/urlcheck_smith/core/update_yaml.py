import logging
import os
from datetime import datetime
from importlib import resources
from pathlib import Path

import requests
import yaml

# --- CONFIGURATION ---
# Use importlib.resources to find files relative to the package
try:
    with resources.path("urlcheck_smith.data", "ucsmith_db.yaml") as p:
        YAML_FILE = str(p)
except Exception:
    # Fallback to local file if path lookup fails (e.g. not installed)
    YAML_FILE = str(Path(__file__).parent.parent / "data" / "ucsmith_db.yaml")

# Denylist should live next to the packaged data file, with a safe fallback.
try:
    with resources.path("urlcheck_smith.data", "denylist.txt") as p:
        LOCAL_DENYLIST = str(p)
except Exception:
    LOCAL_DENYLIST = str(Path(__file__).parent.parent / "data" / "denylist.txt")
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', None)
API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# --- QUIET MODE TOGGLE ---
QUIET_MODE = False

# --- LOGGING SETUP ---
LOG_LEVEL = logging.WARNING if QUIET_MODE else logging.INFO
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_db():
    if not os.path.exists(YAML_FILE):
        return {"metadata": {}, "user_defined": [], "global_rules": [], "discovered_cache": []}
    with open(YAML_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
        # Ensure consistency with renamed keys
        for key in ['user_defined', 'global_rules', 'discovered_cache']:
            if key not in data or data[key] is None:
                data[key] = []
        return data


def save_db(data):
    with open(YAML_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)


# --- EDITOR FUNCTIONS ---

def add_user_domain(name, category="General"):
    """Adds a new domain to the user_defined arrowlist."""
    db = load_db()
    if any(d['name'] == name for d in db['user_defined']):
        logger.warning(f"Editor: {name} already exists in user_defined.")
        return
    db['user_defined'].append({"name": name, "category": category})
    save_db(db)
    logger.info(f"Editor: Added {name} ({category}) to user_defined.")


def remove_user_domain(name):
    """Removes a domain from the user_defined arrowlist."""
    db = load_db()
    original_count = len(db['user_defined'])
    db['user_defined'] = [d for d in db['user_defined'] if d['name'] != name]
    if len(db['user_defined']) < original_count:
        save_db(db)
        logger.info(f"Editor: Removed {name} from user_defined.")
    else:
        logger.warning(f"Editor: {name} not found in user_defined.")


def modify_user_category(name, new_category):
    """Updates the category for an existing user_defined domain."""
    db = load_db()
    for entry in db['user_defined']:
        if entry['name'] == name:
            entry['category'] = new_category
            save_db(db)
            logger.info(f"Editor: Updated {name} category to {new_category}.")
            return
    logger.warning(f"Editor: {name} not found to modify.")


def clear_user_domains():
    """Wipes all entries from the user_defined arrowlist."""
    db = load_db()
    db['user_defined'] = []
    save_db(db)
    logger.info("Editor: Cleared all user_defined entries.")


# --- CORE LOGIC ---

def check_google_fact_check(domain):
    """
    Scouts for known misinformation flags for a given domain using the Google Fact Check Tools API.
    This function requires the 'GOOGLE_API_KEY' environment variable to be set.
    If the API key is missing, it returns None, and the domain enrichment will fallback
    to local shields and denylists.
    """
    if not GOOGLE_API_KEY:
        return None
    params = {'query': f'site:{domain}', 'key': GOOGLE_API_KEY}
    try:
        response = requests.get(API_URL, params=params)
        data = response.json()
        claims = data.get('claims', [])
        negative_flags = 0
        neg_terms = {'false', 'misleading', 'incorrect', 'fake', 'pants on fire', 'distorted', 'conspiracy'}
        for claim in claims:
            reviews = claim.get('claimReview', [])
            if reviews:
                rating = reviews[0].get('textualRating', '').lower()
                if any(term in rating for term in neg_terms):
                    negative_flags += 1
        return negative_flags
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None


def enrich_domain(domain):
    db = load_db()
    domain = domain.lower().strip()

    # 1. SHIELD (User Defined)
    for entry in db['user_defined']:
        if entry.get('name') == domain:
            logger.info(f"SHIELD HIT (User Defined): {domain} verified.")
            return

    # 2. SHIELD (Global Rules)
    for entry in db.get('global_rules', []):
        name = entry.get('name')
        if name and (domain == name or domain.endswith(f".{name}")):
            logger.info(f"SHIELD HIT (Global Rule): {domain} verified by '{name}'")
            return

    # 3. SECONDARY SCOUT (Denylist)
    if os.path.exists(LOCAL_DENYLIST):
        with open(LOCAL_DENYLIST, 'r') as f:
            if domain in {line.strip().lower() for line in f if line.strip()}:
                logger.warning(f"DENYLIST HIT: {domain} found in local denylist.")
                return _update_cache(db, domain, 99, 0.0)

    # 4. PRIMARY SCOUT (API)
    logger.info(f"SCOUTING: Querying API for {domain}...")
    flag_count = check_google_fact_check(domain)

    score = 0.5
    if flag_count is not None:
        if flag_count == 1:
            score = 0.4
        elif 1 < flag_count <= 4:
            score = 0.2
        elif flag_count > 4:
            score = 0.1

    return _update_cache(db, domain, flag_count or 0, score)


def _update_cache(db, domain, flag_count, score):
    new_entry = {
        'name': domain,
        'flags_found': flag_count,
        'credibility_score': score,
        'last_check': datetime.now().strftime('%Y-%m-%d')
    }
    cache = db['discovered_cache']
    match_index = next((i for i, x in enumerate(cache) if x['name'] == domain), None)

    if match_index is not None:
        cache[match_index] = new_entry
        logger.info(f"CACHE UPDATE: {domain} refreshed (Score: {score})")
    else:
        cache.append(new_entry)
        logger.info(f"CACHE ADD: {domain} registered (Score: {score})")

    save_db(db)
