# docs/source/conf.py
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
else:
    sys.path.insert(0, str(ROOT))

project = "urlcheck-smith"
author = "Eiichi Yamamoto"
copyright = "2026, Eiichi Yamamoto"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

# Allow docs to build even when runtime deps aren't installed (e.g. when Sphinx
# is invoked from an isolated environment like pipx).
autodoc_mock_imports = [
    "yaml",  # PyYAML
    "requests",
    "urlextract",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": False,
}

autosummary_generate = True
