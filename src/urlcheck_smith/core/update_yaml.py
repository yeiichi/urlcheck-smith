import logging
import os
from datetime import datetime
from importlib import resources
from pathlib import Path

import requests
import yaml

# --- CONFIGURATION ---
PACKAGE = "urlcheck_smith.resources"
RESOURCE_DB_NAME = "ucsmith_db.yaml"
RESOURCE_DENYLIST_NAME = "denylist.txt"
DEFAULT_USER_DB_NAME = "usmith_db.yaml"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)
API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# --- QUIET MODE TOGGLE ---
QUIET_MODE = False

# --- LOGGING SETUP ---
LOG_LEVEL = logging.WARNING if QUIET_MODE else logging.INFO
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _resource_path(resource_name: str) -> Path:
    return Path(resources.files(PACKAGE).joinpath(resource_name))


def _baseline_db_path() -> Path:
    return _resource_path(RESOURCE_DB_NAME)


def _cwd_db_path() -> Path:
    return Path.cwd() / DEFAULT_USER_DB_NAME


def load_db(db_path: str | Path | None = None):
    """
    Load a YAML database.

    Resolution order:
    1. explicit db_path
    2. ./usmith_db.yaml in the current working directory
    3. packaged baseline resource
    """
    if db_path is None:
        candidate = _cwd_db_path()
        if candidate.exists():
            db_path = candidate
        else:
            db_path = _baseline_db_path()

    db_path = Path(db_path)
    if not db_path.exists():
        return {"metadata": {}, "user_defined": [], "global_rules": [], "discovered_cache": []}

    with db_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        for key in ["user_defined", "global_rules", "discovered_cache"]:
            if key not in data or data[key] is None:
                data[key] = []
        return data


def save_db(data, db_path: str | Path | None = None):
    """
    Save a YAML database.

    Important:
    - Never writes to packaged resources by default.
    - Writes to the user-writable database in the current working directory unless
      an explicit path is provided.
    """
    target = Path(db_path) if db_path is not None else _cwd_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)


# --- EDITOR FUNCTIONS ---

def add_user_domain(name, category="General"):
    """Adds a new domain to the user_defined list."""
    db = load_db()
    if any(d["name"] == name for d in db["user_defined"]):
        logger.warning(f"Editor: {name} already exists in user_defined.")
        return
    db["user_defined"].append({"name": name, "category": category})
    save_db(db)
    logger.info(f"Editor: Added {name} ({category}) to user_defined.")


def remove_user_domain(name):
    """Removes a domain from the user_defined list."""
    db = load_db()
    original_count = len(db["user_defined"])
    db["user_defined"] = [d for d in db["user_defined"] if d["name"] != name]
    if len(db["user_defined"]) < original_count:
        save_db(db)
        logger.info(f"Editor: Removed {name} from user_defined.")
    else:
        logger.warning(f"Editor: {name} not found in user_defined.")


def modify_user_category(name, new_category):
    """Updates the category for an existing user_defined domain."""
    db = load_db()
    for entry in db["user_defined"]:
        if entry["name"] == name:
            entry["category"] = new_category
            save_db(db)
            logger.info(f"Editor: Updated {name} category to {new_category}.")
            return
    logger.warning(f"Editor: {name} not found to modify.")


def clear_user_domains():
    """Wipes all entries from the user_defined list."""
    db = load_db()
    db["user_defined"] = []
    save_db(db)
    logger.info("Editor: Cleared all user_defined entries.")


# --- CORE LOGIC ---

def check_google_fact_check(domain):
    """
    Scouts for known misinformation flags for a given domain using the Google Fact Check Tools API.
    """
    if not GOOGLE_API_KEY:
        return None
    params = {"query": f"site:{domain}", "key": GOOGLE_API_KEY}
    try:
        response = requests.get(API_URL, params=params)
        data = response.json()
        claims = data.get("claims", [])
        negative_flags = 0
        neg_terms = {"false", "misleading", "incorrect", "fake", "pants on fire", "distorted", "conspiracy"}
        for claim in claims:
            reviews = claim.get("claimReview", [])
            if reviews:
                rating = reviews[0].get("textualRating", "").lower()
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
    for entry in db["user_defined"]:
        if entry.get("name") == domain:
            logger.info(f"SHIELD HIT (User Defined): {domain} verified.")
            return

    # 2. SHIELD (Global Rules)
    for entry in db.get("global_rules", []):
        name = entry.get("name")
        if name and (domain == name or domain.endswith(f".{name}")):
            logger.info(f"SHIELD HIT (Global Rule): {domain} verified by '{name}'")
            return

    # 3. SECONDARY SCOUT (Denylist)
    denylist_path = _resource_path(RESOURCE_DENYLIST_NAME)
    if denylist_path.exists():
        with denylist_path.open("r", encoding="utf-8") as f:
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
        "name": domain,
        "flags_found": flag_count,
        "credibility_score": score,
        "last_check": datetime.now().strftime("%Y-%m-%d"),
    }
    cache = db["discovered_cache"]
    match_index = next((i for i, x in enumerate(cache) if x["name"] == domain), None)

    if match_index is not None:
        cache[match_index] = new_entry
        logger.info(f"CACHE UPDATE: {domain} refreshed (Score: {score})")
    else:
        cache.append(new_entry)
        logger.info(f"CACHE ADD: {domain} registered (Score: {score})")

    save_db(db)