SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE ?= .env
COMPOSE_FILE ?= docker-compose.yml
COMPOSE_CMD := $(COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

export DOCKER_BUILDKIT ?= 1
export COMPOSE_DOCKER_CLI_BUILD ?= 1

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available pipeline commands
	@printf "\nJapan Analysis - Airflow/dbt pipeline commands\n\n"
	@printf "Usage:\n"
	@printf "  make -C pipeline <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\nExamples:\n"
	@printf "  make -C pipeline config\n"
	@printf "  make -C pipeline build\n"
	@printf "  make -C pipeline up-d\n"
	@printf "  make -C pipeline recreate\n"
	@printf "  make -C pipeline check-source-db\n"
	@printf "  make -C pipeline dbt-run\n\n"

.PHONY: config
config: ## Validate and render Airflow/dbt pipeline compose config
	$(COMPOSE_CMD) --profile tools config

.PHONY: build
build: ## Build the local Airflow image with dbt and loader dependencies
	$(COMPOSE_CMD) --profile build build airflow-image

.PHONY: up-d
up-d: build ## Build image, then start warehouse Postgres, Airflow webserver, and scheduler
	$(COMPOSE_CMD) up -d warehouse-postgres warehouse-init airflow-init airflow-webserver airflow-scheduler

.PHONY: recreate
recreate: build ## Recreate pipeline services so changed .env values are applied
	$(COMPOSE_CMD) up -d --force-recreate warehouse-postgres warehouse-init airflow-init airflow-webserver airflow-scheduler

.PHONY: ps
ps: ## Show Airflow/dbt pipeline service status
	$(COMPOSE_CMD) ps

.PHONY: check-source-db
check-source-db: build ## Check source Postgres credentials from the pipeline container
	$(COMPOSE_CMD) --profile build run --rm --entrypoint python airflow-image -c "from loaders.suumo_batch_loader import load_source_postgres_config, postgres_connection; config = load_source_postgres_config(); connection = postgres_connection(config); connection.close(); print(f'OK source postgres: {config.user}@{config.host}:{config.port}/{config.dbname}')"

.PHONY: logs
logs: ## Follow pipeline logs, optionally pass service=airflow-scheduler
	$(COMPOSE_CMD) logs -f $(service)

.PHONY: down
down: ## Stop Airflow/dbt pipeline containers, keep warehouse volume
	$(COMPOSE_CMD) down --remove-orphans

.PHONY: clean-volumes
clean-volumes: ## Stop pipeline containers and delete warehouse/Airflow metadata volume
	$(COMPOSE_CMD) down --volumes --remove-orphans

.PHONY: dbt-debug
dbt-debug: ## Run dbt debug against warehouse
	$(COMPOSE_CMD) run --rm dbt-runner dbt debug

.PHONY: dbt-run
dbt-run: ## Run dbt models against warehouse
	$(COMPOSE_CMD) run --rm dbt-runner dbt run

.PHONY: dbt-test
dbt-test: ## Run dbt tests against warehouse
	$(COMPOSE_CMD) run --rm dbt-runner dbt test
