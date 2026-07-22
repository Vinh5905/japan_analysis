SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE := .env
export DOCKER_BUILDKIT ?= 1
export COMPOSE_DOCKER_CLI_BUILD ?= 1

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available root commands
	@printf "\nJapan Analysis - shared infrastructure commands\n\n"
	@printf "Usage:\n"
	@printf "  make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\nExamples:\n"
	@printf "  make infra-up-d\n"
	@printf "  make infra-ps\n"
	@printf "  make infra-logs service=postgres\n\n"

.PHONY: infra-config
infra-config: ## Validate and render the shared infrastructure compose config
	$(COMPOSE) --env-file $(ENV_FILE) config

.PHONY: infra-pull
infra-pull: ## Pull shared infrastructure images
	$(COMPOSE) --env-file $(ENV_FILE) pull

.PHONY: infra-up
infra-up: ## Start shared PostgreSQL and MinIO in foreground
	$(COMPOSE) --env-file $(ENV_FILE) up

.PHONY: infra-up-d
infra-up-d: ## Start shared PostgreSQL and MinIO in background
	$(COMPOSE) --env-file $(ENV_FILE) up -d

.PHONY: infra-down
infra-down: ## Stop shared infrastructure, keep volumes
	$(COMPOSE) --env-file $(ENV_FILE) down

.PHONY: infra-restart
infra-restart: ## Restart shared infrastructure
	$(COMPOSE) --env-file $(ENV_FILE) restart

.PHONY: infra-ps
infra-ps: ## Show shared infrastructure service status
	$(COMPOSE) --env-file $(ENV_FILE) ps

.PHONY: infra-logs
infra-logs: ## Follow shared infrastructure logs, optionally pass service=postgres|minio|minio-init
	$(COMPOSE) --env-file $(ENV_FILE) logs -f $(service)

.PHONY: psql
psql: ## Open psql using credentials from .env inside the shared postgres container
	$(COMPOSE) --env-file $(ENV_FILE) exec postgres sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

.PHONY: minio-shell
minio-shell: ## Open a shell in the shared MinIO container
	$(COMPOSE) --env-file $(ENV_FILE) exec minio sh

.PHONY: minio-ls
minio-ls: ## List MinIO buckets through the one-shot minio-init client image
	$(COMPOSE) --env-file $(ENV_FILE) run --rm minio-init

.PHONY: infra-clean
infra-clean: ## Stop shared infrastructure and remove anonymous containers/networks, keep named volumes
	$(COMPOSE) --env-file $(ENV_FILE) down --remove-orphans

.PHONY: infra-clean-volumes
infra-clean-volumes: ## Stop shared infrastructure and remove named volumes. This deletes local Postgres and MinIO data.
	$(COMPOSE) --env-file $(ENV_FILE) down --volumes --remove-orphans
