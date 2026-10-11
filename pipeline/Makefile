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
	@printf "  make -C pipeline dbt-charts-up\n\n"
	@printf "  make -C pipeline production-config PRODUCTION_ENV_FILE=.env.production.example\n\n"

.PHONY: config
config: ## Validate and render Airflow/dbt pipeline compose config
	$(COMPOSE_CMD) --profile tools --profile charts config

.PHONY: build
build: ## Build the local Airflow image with dbt and loader dependencies
	$(COMPOSE_CMD) --profile build build airflow-image warehouse-postgres

.PHONY: up-d
up-d: dbt-airflow-manifest ## Build image, then start warehouse Postgres, Airflow webserver, and scheduler
	$(COMPOSE_CMD) up -d warehouse-postgres warehouse-init airflow-init airflow-webserver airflow-scheduler

.PHONY: recreate
recreate: dbt-airflow-manifest ## Recreate pipeline services so changed .env values are applied
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

.PHONY: dbt-charts-validate
dbt-charts-validate: build ## Validate board schema and EXPLAIN every query on the local warehouse
	$(COMPOSE_CMD) --profile charts run --rm --no-deps dbt-charts dct validate charts/ --warehouse --project-dir /opt/airflow/dbt

.PHONY: dbt-charts-up
dbt-charts-up: build ## Start dbt Charts at http://localhost:3000
	$(COMPOSE_CMD) --profile charts up -d dbt-charts

.PHONY: dbt-charts-smoke
dbt-charts-smoke: build ## Render all boards and verify BI population/filter semantics (read-only)
	$(COMPOSE_CMD) --profile charts run --rm --no-deps dbt-charts /opt/airflow/dbt_venv/bin/python /opt/airflow/pipeline/tests/verify_dbt_charts.py

.PHONY: dbt-charts-down
dbt-charts-down: ## Stop the local dbt Charts server
	$(COMPOSE_CMD) --profile charts stop dbt-charts

.PHONY: dbt-charts-logs
dbt-charts-logs: ## Follow dbt Charts server and query logs
	$(COMPOSE_CMD) --profile charts logs -f dbt-charts

.PHONY: dbt-charts-render
dbt-charts-render: build ## Render one board; pass board=charts/file.yml format=html
	mkdir -p ../analytics/dbt/renders
	$(COMPOSE_CMD) --profile charts run --rm --no-deps dbt-charts dct render $(or $(board),charts/rental_market_overview.yml) --format $(or $(format),html) --project-dir /opt/airflow/dbt

.PHONY: production-check-env
production-check-env:
	@test -f "$(PRODUCTION_ENV_FILE)" || { printf "Missing %s; copy .env.production.example and set production credentials\n" "$(PRODUCTION_ENV_FILE)"; exit 2; }

.PHONY: production-config
production-config: production-check-env ## Validate production compose and env without displaying secrets
	$(PRODUCTION_COMPOSE_CMD) --profile docs config -q

.PHONY: production-up-d
production-up-d: production-check-env ## Build and start the production pipeline with resource limits
	$(PRODUCTION_COMPOSE_CMD) --profile build build airflow-image
	$(PRODUCTION_COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m dbt_airflow.manifest
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

.PHONY: dbt-airflow-manifest
dbt-airflow-manifest: build ## Atomically refresh the static Airflow dbt graph (no warehouse queries)
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m dbt_airflow.manifest

.PHONY: dbt-airflow-check
dbt-airflow-check: ## Verify manifest task coverage, dependencies, selection and failure handling
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m unittest discover -s /opt/airflow/pipeline/tests -p 'test_dbt_airflow.py' -v

.PHONY: geocode-init geocode geocode-test
geocode-init: ## Create the geocode cache source in an existing warehouse (no HTTP)
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_geocoder --init-only

geocode: ## Enrich addresses from existing dbt mart observations; pass opts="--dry-run" or "--limit 5"
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_geocoder $(opts)

geocode-test: ## Run fixture-based Python geocoder and notebook parity tests (no HTTP)
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m unittest discover -s /opt/airflow/pipeline/tests -p 'test_suumo_geocoder.py' -v

.PHONY: building-backfill building-init building-test
building-init: ## Create the building-name audit source, preserving existing data
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_building_backfill --init-only

building-backfill: ## Backfill existing HTML names locally; pass opts="--dry-run --limit 5"
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_building_backfill $(opts)

building-test: ## Run building extraction and backfill regression tests without crawling
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m unittest discover -s /opt/airflow/pipeline/tests -p 'test_suumo_building*.py' -v

.PHONY: building-location-init building-location building-location-test
building-location-init: ## Create building POI cache without HTTP; preserve existing warehouse data
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_building_locator --init-only

building-location: ## Lookup new/due building candidates; opts="--dry-run" or "--limit 5"
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.suumo_building_locator $(opts)

building-location-test: ## Test HTTP fixtures, matching and cache without live requests
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m unittest discover -s /opt/airflow/pipeline/tests -p 'test_suumo_building_locator.py' -v

.PHONY: building-location-verify building-location-cache-test
building-location-verify: ## Verify protected baseline and export coverage; opts="--capture-baseline" before migration
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image /opt/airflow/pipeline/tests/verify_building_locations_warehouse.py $(opts)

building-location-cache-test: ## Real PostgreSQL cache fixtures, no HTTP; rolls back every write
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image /opt/airflow/pipeline/tests/integration_building_locations_cache.py

.PHONY: mlit-init mlit-refresh mlit-test mlit-verify mlit-publication
mlit-init: ## Create PostGIS/MLIT raw and operational tables, preserving warehouse data
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.mlit_zoning_loader --init-only

mlit-refresh: ## Check official MLIT ZIP/XLSX and import raw; opts="--dry-run" makes no requests/writes
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.mlit_zoning_loader $(opts)

mlit-publication: ## Review/publish/rollback/export a run; pass opts="check --run-id ..."
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m loaders.mlit_zoning_publication $(opts)

mlit-test: ## HTTP/archive fixtures, graph tests and transactional PostGIS/publication fixtures
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image -m unittest discover -s /opt/airflow/pipeline/tests -p 'test_mlit_zoning*.py' -v
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image /opt/airflow/pipeline/tests/integration_mlit_zoning.py

mlit-verify: ## Check baseline/grain and export building/observation coverage locally
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image /opt/airflow/pipeline/tests/verify_mlit_zoning_warehouse.py
	$(COMPOSE_CMD) --profile build run --rm --no-deps --entrypoint python airflow-image /opt/airflow/pipeline/tests/verify_mlit_zoning_storage.py
