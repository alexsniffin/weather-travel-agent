.PHONY: help install install-dev run dev lint format check clean test

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	uv sync --no-dev

install-dev: ## Install development dependencies
	uv sync

# Run the application with python -m (uses __main__)
run: ## Run the application
	uv run python -m weather_travel_agent.main

# Run in dev mode with autoreload (uses uvicorn CLI)
dev:
	DEV_MODE=true;uv run python -m src.main

# Code quality
lint: ## Run ruff linter
	uv run ruff check src/ --fix

format: ## Format code with ruff
	uv run ruff format src/

check: ## Run linting and formatting checks
	uv run ruff check src/
	uv run ruff format --check src/

# Testing
test: ## Run unit tests
	uv run python -m pytest -q

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html

all: format lint test ## Run all checks (format, lint, test)
