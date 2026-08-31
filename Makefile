.PHONY: help up down restart status logs build test test-docker lint format clean ps

# Default target
.DEFAULT_GOAL := help

help: ## Display this help message
	@echo "UDT-X Platform Automation"
	@echo "========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all services in the background
	docker compose up -d

down: ## Stop all running services
	docker compose down

down-v: ## Stop all services and remove named volumes
	docker compose down -v

restart: ## Restart all services
	docker compose restart

status: ## Show status of running containers
	docker compose ps

ps: status

logs: ## Tail logs of all running services
	docker compose logs -f

logs-api: ## Tail logs of the FastAPI service
	docker compose logs -f api

build: ## Build all Docker images
	docker compose build

test: ## Run full pytest test suite
	pytest -v

test-docker: ## Run pytest inside temporary container
	docker compose run --rm api pytest tests/ -v

lint: ## Run ruff linter and formatting check
	ruff check schema tests services && ruff format --check schema tests services

format: ## Format Python source code with ruff
	ruff format schema tests services && ruff check --fix schema tests services

clean: ## Clean Python cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
