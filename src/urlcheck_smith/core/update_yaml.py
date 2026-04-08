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
    """
    Constructs and returns a Path object for the given resource name located
    within the package's resource files.

    Args:
        resource_name (str): Name of the resource file to locate.

    Returns:
        Path: A pathlib.Path object representing the full path to the resource.
    """
    return Path(resources.files(PACKAGE).joinpath(resource_name))


def _baseline_db_path() -> Path:
    """
    Generates the baseline database path.

    This function constructs and returns the full path to the
    baseline database resource by combining the resource base
    path with the database filename.

    Returns:
        Path: The full path to the baseline database file.
    """
    return _resource_path(RESOURCE_DB_NAME)


def _cwd_db_path() -> Path:
    """
    Generates the full path of the default user database in the current working directory.

    This function constructs a `Path` object that combines the current working
    directory (`Path.cwd()`) with the default database filename
    (`DEFAULT_USER_DB_NAME`). It simplifies the process of locating the
    user database within the current workspace.

    Returns:
        Path: The complete path to the default user database file in the
        current working directory.
    """
    return Path.cwd() / DEFAULT_USER_DB_NAME


def load_db(db_path: str | Path | None = None):
    """
    Loads the database from the specified path or falls back to a default path if none is provided.
    If the database file does not exist, initializes an empty database structure.

    Args:
        db_path (str | Path | None): The path to the database file. Can be a string, Path object,
            or None. If None, a default path will be used.

    Returns:
        dict: A dictionary containing the database structure with the following keys:
            - "metadata": A dictionary holding metadata information (empty if database does not exist).
            - "user_defined": A list of user-defined entries.
            - "global_rules": A list of global rules.
            - "discovered_cache": A list representing a discovered cache of data.

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
    Saves the provided data to a YAML file at the specified database path. If no path
    is provided, it defaults to the current working directory database path.

    This function ensures that the target directory exists before saving the YAML
    file. The data is written with UTF-8 encoding and supports Unicode characters.

    Args:
        data: The data to be saved in the YAML file.
        db_path (str | Path | None): The target file path where the YAML data is to
            be saved. If None, the default database path in the current working
            directory is used.

    """
    target = Path(db_path) if db_path is not None else _cwd_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)


# --- EDITOR FUNCTIONS ---

def add_user_domain(name, category="General"):
    """
    Adds a new user-defined domain to the database if it does not already exist.

    This function checks the `user_defined` list in the database for an existing
    domain with the given name. If a domain with the same name already exists,
    a warning is logged and no changes are made. If not, the domain is added
    to the `user_defined` list along with its category.

    Args:
        name (str): The name of the user-defined domain to be added.
        category (str, optional): The category of the domain. Defaults to "General".
    """
    db = load_db()
    if any(d["name"] == name for d in db["user_defined"]):
        logger.warning(f"Editor: {name} already exists in user_defined.")
        return
    db["user_defined"].append({"name": name, "category": category})
    save_db(db)
    logger.info(f"Editor: Added {name} ({category}) to user_defined.")


def remove_user_domain(name):
    """
    Removes a user-defined domain from the database if it exists.

    The function checks the database for a domain with the given name in the
    "user_defined" list. If found, it removes the domain and updates the
    database. If the domain is not found, a warning is logged.

    Args:
        name (str): The name of the domain to be removed.
    """
    db = load_db()
    original_count = len(db["user_defined"])
    db["user_defined"] = [d for d in db["user_defined"] if d["name"] != name]
    if len(db["user_defined"]) < original_count:
        save_db(db)
        logger.info(f"Editor: Removed {name} from user_defined.")
    else:
        logger.warning(f"Editor: {name} not found in user_defined.")


def modify_user_category(name, new_category):
    """
    Modifies the category of a user entry in the database.

    This function searches for a user entry in the "user_defined" section of the
    database with a matching name. If found, it updates the entry's category to
    the specified new category and saves the changes back to the database. If
    the entry is not found, it logs a warning.

    Args:
        name (str): The name of the user whose category needs to be updated.
        new_category (str): The new category to assign to the user entry.
    """
    db = load_db()
    for entry in db["user_defined"]:
        if entry["name"] == name:
            entry["category"] = new_category
            save_db(db)
            logger.info(f"Editor: Updated {name} category to {new_category}.")
            return
    logger.warning(f"Editor: {name} not found to modify.")


def clear_user_domains():
    """
    Clears all user-defined domains from the database.

    This function resets the 'user_defined' field in the database to an empty list.
    It ensures that all previously stored user-defined entries are cleared and the
    updated state is saved back to the database. Additionally, an informational
    log is generated to record the action.

    Raises:
        KeyError: If the expected 'user_defined' field is not present in the
            loaded database dictionary.
    """
    db = load_db()
    db["user_defined"] = []
    save_db(db)
    logger.info("Editor: Cleared all user_defined entries.")


# --- CORE LOGIC ---

def check_google_fact_check(domain):
    """
    Checks if the given domain has been flagged for false or misleading claims using
    Google's Fact Check API.

    This function queries Google's Fact Check API to identify claims associated with
    the provided domain and evaluates if these claims have been negatively flagged
    based on predefined negative terms. If the API key is missing, it will return None.

    Args:
        domain (str): The domain to search for in Google's Fact Check API.

    Returns:
        int | None: The count of negative flags found for the domain, or None if the
        API key is missing or an error occurs.
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
    """
    Process and analyze a given domain to determine its status based on various checks.

    This function evaluates the given domain against user-defined rules, global rules, a
    local denylist, and, if necessary, an external API. Based on these evaluations, the
    domain's status is logged and its information is updated in a cache.

    Args:
        domain (str): The domain name to be analyzed and verified. The domain should be
            provided as a string and will be sanitized (lowercased and stripped of
            unnecessary whitespace) before processing.

    Returns:
        dict: Updated cache data for the domain, including verification status, flag
            count, and calculated score. If the domain is verified or denied, the
            function returns the updated cache information. Otherwise, it proceeds with
            checks through an external API for further verification.
    """
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
    """
    Updates the discovered cache in the database with the provided domain information. If the
    domain already exists in the cache, it updates the existing entry. Otherwise, it adds a
    new entry to the cache. The cache entries include the domain name, the number of flags
    associated, credibility score, and the last check date.

    Args:
        db (dict): The database object containing a "discovered_cache" key for the cache.
        domain (str): The domain name to be added or updated in the cache.
        flag_count (int): The number of flags discovered for the domain.
        score (float): The credibility score associated with the domain.

    """
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