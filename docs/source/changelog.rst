Changelog
=========

v0.8.0 (2026-04-29)
-------------------

Chores
~~~~~~
* Modify pyproject.toml and up.lock
  (`2ecae05 <https://github.com/yeiichi/urlcheck-smith/commit/2ecae05f39e98b73e73f553171d6a0a6ca709a36>`_)

Features
~~~~~~~~
* Add extract-https console script and expose run_extract_https
  (`55b7dec <https://github.com/yeiichi/urlcheck-smith/commit/55b7dec8d0fb148a4a41b072e6d5455832ca067d>`_)


v0.7.0 (2026-04-29)
-------------------

Build System
~~~~~~~~~~~~
* Migrate to uv for dependency management
  (`eb3d201 <https://github.com/yeiichi/urlcheck-smith/commit/eb3d201a9974e69907c96b93ca2d6f951fc81bbb>`_)

Features
~~~~~~~~
* **cli**: Add extract-https command and CSV export (URL + SHA-256 hash)
  (`6ecac43 <https://github.com/yeiichi/urlcheck-smith/commit/6ecac43a0edfa4ead8ed1ccf2522ee6e1073596d>`_)


v0.6.0 (2026-04-09)
-------------------

Bug Fixes
~~~~~~~~~
* Make trust-tier URL classification scheme-agnostic (src/urlcheck_smith/core/trust_manager.py)
  (`7d1c01e <https://github.com/yeiichi/urlcheck-smith/commit/7d1c01e8b187a914d885464aaef5c137e270753a>`_)

Chores
~~~~~~
* Change the api key name placeholder to UCSMITH_GOOGLE_API_KEY (src/urlcheck_smith/core/update_yaml.py, README.md)
  (`96e249b <https://github.com/yeiichi/urlcheck-smith/commit/96e249bf08becc060b4af6092493866d77e816e2>`_)

Documentation
~~~~~~~~~~~~~
* Improve API documentation for core and CLI functions
  (`c9c970b <https://github.com/yeiichi/urlcheck-smith/commit/c9c970b4d8b258302c205171d9ccf9a279ea0728>`_)
* Update Sphinx docs for v0.6.0
  (`1afa75c <https://github.com/yeiichi/urlcheck-smith/commit/1afa75c38aad18a0923c289963a77410295d41b7>`_)

Features
~~~~~~~~
* Add no-API mode with a message that tells the API is disabled (src/urlcheck_smith/core/update_yaml.py)
  (`df4939d <https://github.com/yeiichi/urlcheck-smith/commit/df4939d3dda7162d312a19acd3521bab0c11dc0b>`_)

Refactoring
~~~~~~~~~~~
* Reorganize src layout and resource handling
  (`10a50fb <https://github.com/yeiichi/urlcheck-smith/commit/10a50fb1fd95b3723f01f34be3e2faec98ae736b>`_)


v0.5.0 (2026-04-07)
-------------------

Chores
~~~~~~
* Move docs/source/.readthedocs.yaml -> .readthedocs.yaml
  (`8529ee6 <https://github.com/yeiichi/urlcheck-smith/commit/8529ee60d9662957118d42de742c6f28c0dcf5e3>`_)
* Sort the entries in ucsmith_db.yaml (src/urlcheck_smith/data/ucsmith_db.yaml)
  (`0ce9f5a <https://github.com/yeiichi/urlcheck-smith/commit/0ce9f5a2fc527369faa007a32297a50aeb4ed23a>`_)
* Update project metadata and tests
  (`2193df4 <https://github.com/yeiichi/urlcheck-smith/commit/2193df4ef0b32eed67710debdd3dfe1ed2583ff6>`_)
* **cli**: Generate timestamped default output filenames
  (`eaf21d2 <https://github.com/yeiichi/urlcheck-smith/commit/eaf21d2a927be13834635bc254d46607fd77b000>`_)

Documentation
~~~~~~~~~~~~~
* Add .readthedocs.yaml
  (`4b9e6d5 <https://github.com/yeiichi/urlcheck-smith/commit/4b9e6d5b3186d50945d148a7efad409e70f9b747>`_)
* Correct Version specifiers
  (`e04fca4 <https://github.com/yeiichi/urlcheck-smith/commit/e04fca426b05a7eb91959ca1316d4987929de944>`_)
* Update README
  (`aac83b8 <https://github.com/yeiichi/urlcheck-smith/commit/aac83b8e91ec6bc563f9743684a12a0f35698427>`_)
* Update Sphinx docs
  (`b102506 <https://github.com/yeiichi/urlcheck-smith/commit/b102506e35fa02a53f29b9d512fa5ce9aaf17c83>`_)

Features
~~~~~~~~
* Add default user agent, update URL checking, and refresh trust/classification data
  (`ea93fde <https://github.com/yeiichi/urlcheck-smith/commit/ea93fdee7c143a5b72c6779be80f1817a1b90be2>`_)

Refactoring
~~~~~~~~~~~
* Modernize core logic and improve URL extraction
  (`b033e7c <https://github.com/yeiichi/urlcheck-smith/commit/b033e7c17e530fe056c0f3453b6e5a50245a3e10>`_)


v0.3.1 (2026-04-05)
-------------------

Chores
~~~~~~
* Release v0.3.1
  (`5cb7fd4 <https://github.com/yeiichi/urlcheck-smith/commit/5cb7fd408d4cbd354f71e880a40ccc438ce7dd13>`_)

Refactoring
~~~~~~~~~~~
* Move processing logic into core package
  (`2a9510b <https://github.com/yeiichi/urlcheck-smith/commit/2a9510b3f37d5adaaca278e646a9f559b35462df>`_)
* Move processing modules into core package
  (`e9585aa <https://github.com/yeiichi/urlcheck-smith/commit/e9585aa8826bd292216844219885751cd6f99ca4>`_)


v0.3.0 (2026-03-13)
