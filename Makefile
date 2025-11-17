.PHONY: help install install-dev test lint format clean run

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-package: ## Install package in editable mode
	pip install -e .

test: ## Run tests with pytest
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint: ## Run linting checks (flake8 and mypy)
	flake8 src/ tests/
	mypy src/

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

format-check: ## Check if code is formatted correctly
	black --check src/ tests/
	isort --check-only src/ tests/

clean: ## Clean up cache files and build artifacts
	rm -rf cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.csv' -delete
	find . -type f -name '*.json' -delete

run: ## Run the scraper with default settings
	python -m ethicalmeat.cli

run-nocache: ## Run the scraper without caching
	python -m ethicalmeat.cli --no-cache

scrape-json: ## Scrape and output only JSON
	python -m ethicalmeat.cli --format json

scrape-csv: ## Scrape and output only CSV
	python -m ethicalmeat.cli --format csv

check: format-check lint test ## Run all checks (format, lint, test)

dev-setup: install-dev install-package ## Complete development setup
	@echo "✨ Development environment ready!"
