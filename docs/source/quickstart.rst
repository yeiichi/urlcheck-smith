Quickstart
==========

This page gives a short introduction to the most common use cases.

Extract HTTPS URLs (CSV)
-------------------------

If you only need a clean list of unique HTTPS URLs from a text file, use ``extract-https``:

.. code-block:: bash

   extract-https --input sample.txt --output https_urls.csv

Scan and Classify URLs
----------------------

The most common use case is to scan a text file for URLs and classify them.

.. code-block:: bash

   urlcheck-smith scan sample.txt -o urls.csv

This will extract URLs, classify them by domain suffix, perform HTTP checks, and save the result to ``urls.csv``.

Single URL Classification (CLI)
-------------------------------

You can classify a single URL and see why it was categorized a certain way.

.. code-block:: bash

   urlcheck-smith classify-url https://www.itu.int/en/Pages/default.aspx --explain

API Example (Library Usage)
---------------------------

If you want to classify a URL from Python, you can use the public API directly.
The example below shows a small helper script that demonstrates how to create a URL record and classify it.

.. code-block:: python

   from urlcheck_smith import SiteClassifier, UrlRecord

   def classify_single_url(
           url: str,
           *,
           rules_path: str | None = None,
           explain: bool = False,
   ) -> dict:
       classifier = SiteClassifier(
           rules_path=rules_path,
           explain=explain,
           normalize_domain=True,
       )

       rec = classifier.classify([UrlRecord(url=url)])[0]

       result = {
           "url": rec.url,
           "base_url": rec.base_url,
           "category": rec.category,
           "trust_tier": rec.trust_tier,
       }

       if rec.explain:
           result["explain"] = rec.explain

       return result

   data = classify_single_url("https://www.itu.int/en/Pages/default.aspx", explain=True)
   print(data)

Batch Classification (No HTTP)
------------------------------

If you have a list of URLs and only want to classify them without performing HTTP checks:

.. code-block:: bash

   urlcheck-smith classify urls.txt -o classified.csv

JSONL Output
------------

Both ``scan`` and ``classify`` support JSONL output:

.. code-block:: bash

   urlcheck-smith scan sample.txt --format jsonl -o urls.jsonl

Rule Presets
------------

You can use built-in presets for specific regions:

.. code-block:: bash

   urlcheck-smith scan urls.txt --preset japan -o out.csv
   urlcheck-smith scan urls.txt --preset eu -o out.csv
