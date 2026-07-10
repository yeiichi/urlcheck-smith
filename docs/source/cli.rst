CLI Reference
=============

urlcheck-smith provides several commands.

extract-https
-------------

Extract unique HTTPS URLs from a text file and export them to CSV (columns: ``URL``, ``hashed_URL``).

You can run it either as a standalone console script:

.. code-block:: bash

   extract-https --input sample.txt --output https_urls.csv

Or via the main ``urlcheck-smith`` CLI:

.. code-block:: bash

   urlcheck-smith extract-https --input sample.txt --output https_urls.csv

If ``--input`` / ``--output`` are omitted, the command prompts interactively. Leaving the output blank uses a timestamped default like ``https_urls_YYYYMMDD_HHMMSS.csv``.

**Common options:**

- ``-i, --input <file>``: Source text file (optional; prompts if omitted).
- ``-o, --output <file>``: Output CSV path (optional; prompts if omitted).

crawl
-----

Crawl an HTML URL and export discovered page/document URLs to CSV (columns: ``URL``, ``anchor_text``, ``hashed_URL``).

.. code-block:: bash

   urlcheck-smith crawl https://example.com --output-path crawl_urls.csv

If ``src_uri`` is omitted, the command prompts for it on stdin. If ``--output-path`` is omitted, the command writes a source-URL-based ``.csv`` filename in the current directory. Crawling defaults to depth 0 and 50 fetched pages to keep broad sites from expanding too far. The command waits 0.5 seconds between page fetches by default. Default output is limited to HTML-like pages plus PDF, TXT, CSV, DOCX, XLSX, and PPTX URLs.

**Common options:**

- ``src_uri``: Source URL (optional; prompts if omitted).
- ``--output-path <file>``: Output CSV path.
- ``--max-pages <n>``: Maximum pages to fetch, including the source page (default: 50).
- ``--depth <0|1|2>``: Deepest link layer to collect (default: 0).
- ``--timeout <seconds>``: HTTP timeout per page fetch (default: 5.0).
- ``--request-interval <seconds>``: Delay between page fetches (default: 0.5).
- ``--include-assets``: Include URLs outside the default page/document target types, such as JavaScript, CSS, images, and fonts.

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
- ``update <domain>``: Enrich a single domain via Google Fact Check API.
- ``update --file <file>``: Update domains listed in a file.
- ``update --all``: Update all previously discovered domains in the cache.

**Requirements for Update:**
- Set ``UCSMITH_GOOGLE_API_KEY`` (Google Fact Check Tools API key) in your environment.
- An internet connection is required.
- Results are stored in the local ``ucsmith_db.yaml`` cache.

API Key (Optional)
------------------

A Google API key is **only required** for domain enrichment via the ``db update`` command. All core features (scanning, classification, HTTP checks) work without it.

The package reads the API key from:

.. code-block:: bash

   export UCSMITH_GOOGLE_API_KEY="your-api-key"

Rule Precedence
---------------

When multiple rule sources are used, they are prioritized as follows:

1. **User defined** in database (``db add`` command)
2. **User rules files** (``--rules`` flag)
3. **Global rules** in database (``ucsmith_db.yaml``)

The system uses a **Longest-Suffix-Match** strategy. More specific rules (e.g., ``blog.google.com``) will match before more general ones (e.g., ``google.com``).
