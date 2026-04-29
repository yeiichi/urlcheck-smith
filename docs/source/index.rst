.. _index:

urlcheck-smith documentation
============================

Welcome to the documentation for ``urlcheck-smith``.

A compact, fast URL analysis pipeline:

- Extract URLs from arbitrary text files
- Classify domains using suffix-based “site runner” rules (government, edu, private, etc.)
- Trust Tier classification (Official, News, General)
- Optional HTTP checks (status, redirect, CAPTCHA/human-check heuristic)
- Output results as CSV or JSONL
- Standalone URL classifier (``classify-url``)
- Interactive HTTPS URL extractor (``extract-https``) with CSV export
- Batch classification mode (``classify``)
- Database management command (``db``) to enrich or add custom trusted domains
- Supports custom YAML rules, explain mode, quiet mode
- **Classification**: Assigns categories (e.g., government, education) based on domain suffix rules from the built-in UC Smith database.
- **HTTP Verification**: Checks reachability and captures status codes.
- **Soft 404 Detection**: Identifies pages that return a ``200 OK`` status but contain "Page Not Found" text.
- **Trust Tier Analysis**: Automatically categorizes URLs into ``TIER_1_OFFICIAL``, ``TIER_2_RELIABLE``, or ``TIER_3_GENERAL`` using ``TrustManager``.
- **Human-Check Detection**: Flags URLs that likely lead to CAPTCHA or bot-detection screens.
- **Enrichment**: Query the Google Fact Check API to scout for known misinformation flags and update the credibility score.

Features in Detail
------------------

Soft 404 Detection
~~~~~~~~~~~~~~~~~~

Many websites are configured to return a standard ``200 OK`` status even when a page is missing, often displaying a custom "not found" message to users. ``urlcheck-smith`` detects this by scanning the first 2000 characters of the response for common markers like:

- "page not found"
- "error 404"
- "the page you requested cannot be found"

If a marker is found, the ``soft_404_detected`` field in the output is set to ``True``, allowing you to filter out these "ghost" pages from your results.

Trust Tier Classification
~~~~~~~~~~~~~~~~~~~~~~~~~

To help prioritize analysis, ``urlcheck-smith`` assigns a trust tier to each URL:

- **TIER_1_OFFICIAL**: Government (``.gov``, ``.go.jp``, etc.), UN, and official international domains.
- **TIER_2_RELIABLE**: Verified news organizations (Reuters, AP, BBC, etc.) and educational institutions.
- **TIER_3_GENERAL**: All other domains.

This is available via the ``trust_tier`` field in CSV/JSONL outputs.

Getting started
---------------

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   use_cases
   cli
   api/index
   development
   changelog
