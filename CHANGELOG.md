# CHANGELOG

<!-- version list -->

## v0.7.0 (2026-04-29)

### Build System

- Migrate to uv for dependency management
  ([`eb3d201`](https://github.com/yeiichi/urlcheck-smith/commit/eb3d201a9974e69907c96b93ca2d6f951fc81bbb))

### Features

- **cli**: Add extract-https command and CSV export
  ([`6ecac43`](https://github.com/yeiichi/urlcheck-smith/commit/6ecac43a0edfa4ead8ed1ccf2522ee6e1073596d))


## v0.6.0 (2026-04-09)

### Bug Fixes

- Make trust-tier URL classification scheme-agnostic (src/urlcheck_smith/core/trust_manager.py)
  ([`7d1c01e`](https://github.com/yeiichi/urlcheck-smith/commit/7d1c01e8b187a914d885464aaef5c137e270753a))

### Chores

- Change the api key name placeholder to UCSMITH_GOOGLE_API_KEY
  (src/urlcheck_smith/core/update_yaml.py, README.md)
  ([`96e249b`](https://github.com/yeiichi/urlcheck-smith/commit/96e249bf08becc060b4af6092493866d77e816e2))

### Documentation

- Improve API documentation for core and CLI functions
  ([`c9c970b`](https://github.com/yeiichi/urlcheck-smith/commit/c9c970b4d8b258302c205171d9ccf9a279ea0728))

- Update Sphinx docs for v0.6.0
  ([`1afa75c`](https://github.com/yeiichi/urlcheck-smith/commit/1afa75c38aad18a0923c289963a77410295d41b7))

### Features

- Add no-API mode with a message that tells the API is disabled
  (src/urlcheck_smith/core/update_yaml.py)
  ([`df4939d`](https://github.com/yeiichi/urlcheck-smith/commit/df4939d3dda7162d312a19acd3521bab0c11dc0b))

### Refactoring

- Reorganize src layout and resource handling
  ([`10a50fb`](https://github.com/yeiichi/urlcheck-smith/commit/10a50fb1fd95b3723f01f34be3e2faec98ae736b))


## v0.5.0 (2026-04-07)

### Chores

- Move docs/source/.readthedocs.yaml -> .readthedocs.yaml
  ([`8529ee6`](https://github.com/yeiichi/urlcheck-smith/commit/8529ee60d9662957118d42de742c6f28c0dcf5e3))

- Sort the entries in ucsmith_db.yaml (src/urlcheck_smith/data/ucsmith_db.yaml)
  ([`0ce9f5a`](https://github.com/yeiichi/urlcheck-smith/commit/0ce9f5a2fc527369faa007a32297a50aeb4ed23a))

- Update project metadata and tests
  ([`2193df4`](https://github.com/yeiichi/urlcheck-smith/commit/2193df4ef0b32eed67710debdd3dfe1ed2583ff6))

- **cli**: Generate timestamped default output filenames
  ([`eaf21d2`](https://github.com/yeiichi/urlcheck-smith/commit/eaf21d2a927be13834635bc254d46607fd77b000))

### Documentation

- Add .readthedocs.yaml
  ([`4b9e6d5`](https://github.com/yeiichi/urlcheck-smith/commit/4b9e6d5b3186d50945d148a7efad409e70f9b747))

- Correct Version specifiers
  ([`e04fca4`](https://github.com/yeiichi/urlcheck-smith/commit/e04fca426b05a7eb91959ca1316d4987929de944))

- Update README
  ([`aac83b8`](https://github.com/yeiichi/urlcheck-smith/commit/aac83b8e91ec6bc563f9743684a12a0f35698427))

- Update Sphinx docs
  ([`b102506`](https://github.com/yeiichi/urlcheck-smith/commit/b102506e35fa02a53f29b9d512fa5ce9aaf17c83))

### Features

- Add default user agent, update URL checking, and refresh trust/classification data
  ([`ea93fde`](https://github.com/yeiichi/urlcheck-smith/commit/ea93fdee7c143a5b72c6779be80f1817a1b90be2))

### Refactoring

- Modernize core logic and improve URL extraction
  ([`b033e7c`](https://github.com/yeiichi/urlcheck-smith/commit/b033e7c17e530fe056c0f3453b6e5a50245a3e10))


## v0.3.1 (2026-04-05)

### Chores

- Release v0.3.1
  ([`5cb7fd4`](https://github.com/yeiichi/urlcheck-smith/commit/5cb7fd408d4cbd354f71e880a40ccc438ce7dd13))

### Refactoring

- Move processing logic into core package
  ([`2a9510b`](https://github.com/yeiichi/urlcheck-smith/commit/2a9510b3f37d5adaaca278e646a9f559b35462df))

- Move processing modules into core package
  ([`e9585aa`](https://github.com/yeiichi/urlcheck-smith/commit/e9585aa8826bd292216844219885751cd6f99ca4))


## v0.3.0 (2026-03-13)

### Chores

- Prepare version 0.3.0 for PyPI release
  ([`991c348`](https://github.com/yeiichi/urlcheck-smith/commit/991c348c024dc542f6783c641c8aa4f9158ce569))


## v0.2.1 (2026-01-22)

### Chores

- Add `readme = "README.md"` to toml (pyproject.toml)
  ([`ca5414f`](https://github.com/yeiichi/urlcheck-smith/commit/ca5414f4f5f7e6acb03ea905870749044f5de887))

- Add src/urlcheck_smith/__init__.py
  ([`93a652d`](https://github.com/yeiichi/urlcheck-smith/commit/93a652dfa73f024fc62c4edd7f8a6ac6696f1de8))

- Bump v0.1.0 -> v0.2.0 (pyproject.toml)
  ([`d3bc346`](https://github.com/yeiichi/urlcheck-smith/commit/d3bc346a94bc3b7103e019e56aa6b67ca7dc3c02))


## v0.2.0 (2026-01-22)


## v0.1.0 (2025-12-11)

- Initial Release
