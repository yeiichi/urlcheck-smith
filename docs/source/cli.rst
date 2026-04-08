CLI Reference
=============

urlcheck-smith provides three main commands.

scan
----

Extract URLs from a text file, classify them, and optionally perform HTTP checks.

.. code-block:: bash

   urlcheck-smith scan <file> [options]

**Common options:**

- ``-o, --output <file>``: Output filename (default: stdout).
- ``--format <csv|jsonl>``: Output format (default: csv).
- ``--no-http``: Skip HTTP status checks.
- ``--preset <japan|eu|global>``: Use a built-in rule preset.
- ``--rules <file>``: Path to a custom YAML rules file.
- ``--quiet``: Machine-friendly output (quiet mode).

classify-url
------------

Classify a single URL and display the results.

.. code-block:: bash

   urlcheck-smith classify-url <url> [options]

**Common options:**

- ``--explain``: Show detailed information about why the URL was classified a certain way.
- ``--quiet``: Machine-friendly output (just JSON).
- ``--rules <file>``: Path to a custom YAML rules file.

classify
--------

Batch classify a list of URLs (one per line) without performing HTTP checks.

.. code-block:: bash

   urlcheck-smith classify <file> [options]

**Common options:**

- ``-o, --output <file>``: Output filename (default: stdout).
- ``--format <csv|jsonl>``: Output format (default: csv).
- ``--explain``: Show detailed information about why the URL was classified a certain way.
- ``--quiet``: Machine-friendly output (quiet mode).

db
--

Manage your local credibility database (``ucsmith_db.yaml``).

.. code-block:: bash

   urlcheck-smith db <command> [args]

**Commands:**

- ``add <domain> --category <category>``: Add a trusted domain.
- ``remove <domain>``: Remove a domain.
- ``update <domain>``: Enrich a domain via Google Fact Check API. Requires ``UCSMITH_GOOGLE_API_KEY`` (Google Fact Check Tools API key) to be set in the environment.

Rule Precedence
---------------

When multiple rule sources are used, they are prioritized as follows:

1. **User defined** in database (``db add`` command)
2. **User rules files** (``--rules`` flag)
3. **Global rules** in database (``ucsmith_db.yaml``)

The system uses a **Longest-Suffix-Match** strategy. More specific rules (e.g., ``blog.google.com``) will match before more general ones (e.g., ``google.com``).
