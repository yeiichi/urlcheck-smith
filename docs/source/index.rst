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
- Batch classification mode (``classify``)
- Supports rule presets (Japan/EU/global), custom YAML rules, explain mode, quiet mode

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

API reference
-------------

.. toctree::
   :maxdepth: 2

   api/index
