Installation
============

Install from PyPI
-----------------

.. code-block:: bash

   pip install urlcheck-smith

Install from source
-------------------

.. code-block:: bash

   git clone https://github.com/yeiichi/urlcheck-smith
   cd urlcheck-smith
   uv sync

Development install
-------------------

If you are developing locally:

.. code-block:: bash

   uv sync --group dev
   uv run pytest
