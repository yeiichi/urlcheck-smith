VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help venv install test

help:
	@echo "urlcheck-smith - helper targets"
	@echo ""
	@echo "  make venv     - create virtualenv in .venv"
	@echo "  make install  - install package (editable) + dev deps"
	@echo "  make test     - run tests (pytest)"

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -U pip
	$(PIP) install -e .[dev]

test:
	$(PYTHON) -m pytest
