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
   pip install .

Development install
-------------------

If you are developing locally:

.. code-block:: bash

   python3 -m venv .venv
   . .venv/bin/activate
   pip install -e .[dev]
   pytest
