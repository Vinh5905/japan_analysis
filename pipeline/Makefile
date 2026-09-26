SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE ?= .env
COMPOSE_FILE ?= docker-compose.yml
COMPOSE_CMD := $(COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE)
PRODUCTION_ENV_FILE ?= .env.production
PRODUCTION_COMPOSE_FILE ?= docker-compose.production.yml
PRODUCTION_COMPOSE_CMD := $(COMPOSE) --env-file $(PRODUCTION_ENV_FILE) -f $(COMPOSE_FILE) -f $(PRODUCTION_COMPOSE_FILE)

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
	@printf "  make -C pipeline dbt-run\n"
	@printf "  make -C pipeline dbt-docs-up\n\n"
	@printf "  make -C pipeline production-config PRODUCTION_ENV_FILE=.env.production.example\n\n"

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

.PHONY: dbt-docs-up
dbt-docs-up: ## Generate and serve dbt lineage/docs at http://localhost:8081
	$(COMPOSE_CMD) --profile docs up -d dbt-docs

.PHONY: dbt-docs-down
dbt-docs-down: ## Stop the dbt docs web server
	$(COMPOSE_CMD) --profile docs stop dbt-docs

.PHONY: dbt-docs-logs
dbt-docs-logs: ## Follow dbt docs generation/server logs
	$(COMPOSE_CMD) --profile docs logs -f dbt-docs

.PHONY: production-check-env
production-check-env:
	@test -f "$(PRODUCTION_ENV_FILE)" || { printf "Missing %s; copy .env.production.example and set production credentials\n" "$(PRODUCTION_ENV_FILE)"; exit 2; }

.PHONY: production-config
production-config: production-check-env ## Validate production compose and env without displaying secrets
	$(PRODUCTION_COMPOSE_CMD) --profile docs config -q

.PHONY: production-up-d
production-up-d: production-check-env ## Build and start the production pipeline with resource limits
	$(PRODUCTION_COMPOSE_CMD) --profile build build airflow-image
	$(PRODUCTION_COMPOSE_CMD) up -d warehouse-postgres warehouse-init airflow-init airflow-webserver airflow-scheduler

.PHONY: production-ps
production-ps: production-check-env ## Show production pipeline services
	$(PRODUCTION_COMPOSE_CMD) ps

.PHONY: production-dbt-docs-up
production-dbt-docs-up: production-check-env ## Generate and serve production dbt docs
	$(PRODUCTION_COMPOSE_CMD) --profile docs up -d dbt-docs

.PHONY: production-down
production-down: production-check-env ## Stop the production pipeline, preserving volumes
	$(PRODUCTION_COMPOSE_CMD) down --remove-orphans

.PHONY: recover-batch
recover-batch: ## Reset one failed/stale loading batch: make -C pipeline recover-batch batch_id=123
	@test -n "$(batch_id)" || { echo 'batch_id is required'; exit 2; }
	$(COMPOSE_CMD) run --rm --entrypoint python dbt-runner -m loaders.recover_batch $(batch_id) $(opts)

.PHONY: dbt-build
dbt-build: ## Build dbt models and tests; optionally pass select="model+"
	$(COMPOSE_CMD) run --rm --no-deps dbt-runner dbt build --exclude tag:suumo_notebook_seed $(if $(select),--select $(select),)

.PHONY: dbt-seed-notebook
dbt-seed-notebook: ## Load and test the 17,927-row notebook snapshot in raw schema
	$(COMPOSE_CMD) run --rm --no-deps dbt-runner dbt seed --full-refresh --select suumo_parser_records_seed
	$(COMPOSE_CMD) run --rm --no-deps dbt-runner dbt test --select suumo_parser_records_seed

.PHONY: dbt-check-repeatability
dbt-check-repeatability: ## Rebuild existing mart and assert unchanged rows/keys
	$(COMPOSE_CMD) run --rm --no-deps --entrypoint python dbt-runner /opt/airflow/pipeline/tests/verify_mart_repeatability.py
