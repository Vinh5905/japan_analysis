SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE := .env
MIGRATIONS_DIR := docker/postgres/migrations
RELEASE_COMPOSE := docker-compose.release.yml
RELEASE_ENV_FILE ?= .env
RELEASE_COMPOSE_CMD := $(COMPOSE) --env-file $(RELEASE_ENV_FILE) -f $(RELEASE_COMPOSE)
DOCKERHUB_IMAGE ?= kevinpham9257/suumo-crawler
tag ?= latest
PLATFORMS ?= linux/amd64,linux/arm64
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
	@printf "  make infra-logs service=postgres\n"
	@printf "  make db-migrate-all\n"
	@printf "  make docker-build-push-release tag=latest\n"
	@printf "  make release-up\n"
	@printf "  make release-crawl-links\n\n"

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

.PHONY: db-migrate
db-migrate: ## Run one SQL migration, pass file=docker/postgres/migrations/name.sql
	@test -n "$(file)" || { printf "Usage: make db-migrate file=docker/postgres/migrations/001_drop_crawl_runs_derived_counts.sql\n"; exit 1; }
	$(COMPOSE) --env-file $(ENV_FILE) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1' < $(file)

.PHONY: db-migrate-all
db-migrate-all: ## Run all SQL migrations under docker/postgres/migrations in filename order
	@set -eu; \
	files=$$(find "$(MIGRATIONS_DIR)" -maxdepth 1 -type f -name '*.sql' | sort); \
	if [ -z "$$files" ]; then printf "No SQL migrations found in %s\n" "$(MIGRATIONS_DIR)"; exit 0; fi; \
	for migration in $$files; do \
		printf "\nRunning migration: %s\n" "$$migration"; \
		$(COMPOSE) --env-file $(ENV_FILE) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1' < "$$migration"; \
	done

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

.PHONY: docker-buildx-bootstrap
docker-buildx-bootstrap:
	@docker buildx inspect suumo-release-builder >/dev/null 2>&1 || docker buildx create --name suumo-release-builder --use
	docker buildx use suumo-release-builder
	docker buildx inspect --bootstrap

.PHONY: docker-build-push-release
docker-build-push-release: docker-buildx-bootstrap ## Build and push multi-platform release image for VPS/server usage
	docker buildx build --platform $(PLATFORMS) -f suumo_source_crawler/Dockerfile.release -t $(DOCKERHUB_IMAGE):$(tag) --push .

.PHONY: docker-login
docker-login: ## Login to Docker Hub before pushing release images
	docker login

.PHONY: docker-inspect-release
docker-inspect-release: ## Inspect the remote release image manifest and supported platforms
	docker buildx imagetools inspect $(DOCKERHUB_IMAGE):$(tag)

.PHONY: release-config
release-config: ## Validate and render release compose config
	$(RELEASE_COMPOSE_CMD) --profile tasks --profile tools config

.PHONY: release-pull
release-pull: ## Pull release images
	$(RELEASE_COMPOSE_CMD) --profile tasks --profile tools pull

.PHONY: release-up
release-up: ## Start release infra and run idempotent DB/MinIO bootstrap
	$(RELEASE_COMPOSE_CMD) up -d postgres minio
	$(RELEASE_COMPOSE_CMD) run --rm crawler-init

.PHONY: release-init
release-init: ## Re-run release bootstrap without recreating service containers
	$(RELEASE_COMPOSE_CMD) run --rm crawler-init

.PHONY: release-ps
release-ps: ## Show release service status
	$(RELEASE_COMPOSE_CMD) ps

.PHONY: release-logs
release-logs: ## Follow release logs, optionally pass service=postgres|minio
	$(RELEASE_COMPOSE_CMD) logs -f $(service)

.PHONY: release-down
release-down: ## Stop release containers, keep named volumes
	$(RELEASE_COMPOSE_CMD) down --remove-orphans

.PHONY: release-clean-volumes
release-clean-volumes: ## Stop release containers and remove named volumes. This deletes release Postgres and MinIO data.
	$(RELEASE_COMPOSE_CMD) down --volumes --remove-orphans

.PHONY: release-crawl-links
release-crawl-links: release-up ## Run suumo_links in a one-shot release container
	$(RELEASE_COMPOSE_CMD) run --rm suumo-links

.PHONY: release-crawl-html
release-crawl-html: release-up ## Run suumo_html in a one-shot release container
	$(RELEASE_COMPOSE_CMD) run --rm suumo-html

.PHONY: release-crawl-page
release-crawl-page: release-up ## Run suumo_page in a one-shot release container
	$(RELEASE_COMPOSE_CMD) run --rm suumo-page

.PHONY: release-minio-preview
release-minio-preview: release-up ## Preview a MinIO object from release runtime, pass path="suumo/..." opts="--write-json"
	$(RELEASE_COMPOSE_CMD) run --rm suumo-tools minio-preview $(path) $(opts)

.PHONY: release-manual-rerun-failed-html
release-manual-rerun-failed-html: release-up ## Rerun failed HTML tasks in release runtime, optionally pass opts="--limit 10"
	$(RELEASE_COMPOSE_CMD) run --rm suumo-tools manual-rerun-failed-html $(opts)

.PHONY: release-shell
release-shell: release-up ## Open a shell inside the release crawler image
	$(RELEASE_COMPOSE_CMD) run --rm suumo-tools crawler-shell

.PHONY: release-db-migrate-all
release-db-migrate-all: release-up ## Run bundled SQL migrations from the release crawler image
	$(RELEASE_COMPOSE_CMD) run --rm crawler-init crawler-init --skip-minio --run-migrations
