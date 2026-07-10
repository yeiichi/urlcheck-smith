Development
===========

Running tests
-------------

You can run tests using ``uv`` or the provided ``Makefile``.

.. code-block:: bash

   uv run pytest
   # or
   make test

Install for development
-----------------------

.. code-block:: bash

   make install

Package build and publish
-------------------------

Version control is handled by Python Semantic Release. To preview the next
release locally:

.. code-block:: bash

   make release-check

To run the release workflow, which creates the version commit, tag, and GitHub
Release:

.. code-block:: bash

   make release

Distribution builds are handled by GitHub Actions. The manual build-only path is:

.. code-block:: bash

   make package-build

Publishing is triggered after the Python Semantic Release workflow completes.
The PyPI upload is handled by GitHub Actions using PyPI Trusted Publisher/OIDC;
no PyPI API token is required:

.. code-block:: bash

   make package-publish

Building the docs locally
-------------------------

To build the HTML documentation locally:

.. code-block:: bash

   make docs

The output will be in ``docs/build/html/index.html``.

Contributing
------------

1. Fork the repository.
2. Create a feature branch.
3. Add tests for new behavior.
4. Update documentation where appropriate.
5. Submit a pull request.
