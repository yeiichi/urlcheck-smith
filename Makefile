UV ?= uv

.PHONY: help venv install test clean docs release-check release package-build package-publish

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@printf "  \033[36m%-15s\033[0m %s\n" "help" "Show this help message"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| grep -v '^help:' \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## create/update the uv-managed .venv
	$(UV) sync --group dev

install: venv ## install package (editable) + dev deps with uv

test: ## run tests (pytest)
	$(UV) run pytest

clean: ## Remove build artifacts and Python cache files
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -not -path "*/.venv/*" -exec rm -rf {} +
	@rm -rf dist/ build/ src/*.egg-info/ .coverage htmlcov/ docs/build/
	@echo "Cleanup complete."

docs: ## build sphinx documentation
	$(UV) run sphinx-build -M html docs/source docs/build

release-check: ## preview the next Python Semantic Release version locally
	$(UV) run semantic-release --noop version

release: ## run Python Semantic Release in GitHub Actions
	gh workflow run release.yml --ref main -f no_operation=false

package-build: ## run the package build workflow in GitHub Actions
	gh workflow run pypi.yml --ref main -f publish=false

package-publish: release ## publish via Python Semantic Release and PyPI Trusted Publisher
