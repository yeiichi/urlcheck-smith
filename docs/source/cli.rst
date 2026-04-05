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

classify-url
------------

Classify a single URL and display the results.

.. code-block:: bash

   urlcheck-smith classify-url <url> [options]

**Common options:**

- ``--explain``: Show detailed information about why the URL was classified a certain way.
- ``--quiet``: Machine-friendly output (just JSON).

classify
--------

Batch classify a list of URLs (one per line) without performing HTTP checks.

.. code-block:: bash

   urlcheck-smith classify <file> [options]
