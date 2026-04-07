Quickstart
==========

This page gives a short introduction to the most common use cases.

Scan and Classify URLs
----------------------

The most common use case is to scan a text file for URLs and classify them.

.. code-block:: bash

   urlcheck-smith scan sample.txt -o urls.csv

This will extract URLs, classify them by domain suffix, perform HTTP checks, and save the result to ``urls.csv``.

Single URL Classification
-------------------------

You can also classify a single URL and see why it was categorized a certain way.

.. code-block:: bash

   urlcheck-smith classify-url https://www.soumu.go.jp/ --explain

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
