VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help venv install test clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@printf "  \033[36m%-15s\033[0m %s\n" "help" "Show this help message"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| grep -v '^help:' \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## create virtualenv in .venv
	python3 -m venv $(VENV)

install: venv ## install package (editable) + dev deps
	$(PIP) install -U pip
	$(PIP) install -e .[dev]

test: ## run tests (pytest)
	$(PYTHON) -m pytest

clean: ## Remove build artifacts and Python cache files
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -not -path "*/.venv/*" -exec rm -rf {} +
	@rm -rf dist/ build/ src/*.egg-info/ .coverage htmlcov/
	@echo "Cleanup complete."