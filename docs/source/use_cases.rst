Use Cases
=========

This page showcases how ``urlcheck-smith`` can be used to solve real-world problems.

Verifying a Large List of Unknown URLs
--------------------------------------

**Scenario**: You have a list of hundreds or thousands of URLs (e.g., from a web crawl, a legacy database, or a set of research papers). You need to know:
1. Which URLs are still reachable (HTTP 200)?
2. Which URLs point to reliable sources (Government, Educational institutions, major News outlets)?
3. Which URLs are potentially suspicious or just private blogs?

**Solution**: Use the ``scan`` command with reliability presets.

Step 1: Prepare your input
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a text file (e.g., ``sources.txt``) containing your URLs, or even arbitrary text containing URLs. ``urlcheck-smith`` will automatically extract them.

Step 2: Run the scan with a preset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To classify URLs based on global reliability standards (like ``.gov``, ``.edu``, and major news domains), use the ``--preset global`` flag:

.. code-block:: bash

   urlcheck-smith scan sources.txt --preset global --output results.csv

Step 3: Analyze the results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The resulting ``results.csv`` will contain columns such as:

* ``url``: The extracted URL.
* ``status_code``: The HTTP status (e.g., 200, 404).
* ``category``: The site category (e.g., ``government``, ``education``, ``news``, ``private``).
* ``trust_tier``: The reliability level (e.g., ``TIER_1_OFFICIAL``, ``TIER_2_RELIABLE``, ``TIER_3_GENERAL``).

**Why this is impressive**:
Instead of manually clicking each link and guessing the site's nature, ``urlcheck-smith`` provides a structured, automated report in seconds. By combining **reachability** (HTTP check) with **reliability** (suffix/domain-based classification), you can immediately filter for high-quality, active references.

Example Output (simplified)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 40 10 20 30
   :header-rows: 1

   * - URL
     - Status
     - Category
     - Trust Tier
   * - https://www.data.gov/
     - 200
     - government
     - TIER_1_OFFICIAL
   * - https://www.bbc.co.uk/news
     - 200
     - news
     - TIER_2_RELIABLE
   * - http://expired-link.com/old
     - 404
     - private
     - TIER_3_GENERAL

This allows researchers and data scientists to quickly validate their datasets and focus on the most trustworthy sources.
