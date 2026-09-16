SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE := ../.env
PYTHON ?= python3
PYTHON_ARGS := $(if $(args),$(args),$(filter-out python3 python3-container,$(MAKECMDGOALS)))
CONTAINER_WORKDIR := $(if $(workdir),-w $(workdir),)
PRODUCTION_ENV_FILE ?= ../.env.production
PRODUCTION_ENV_PATH := $(abspath $(PRODUCTION_ENV_FILE))
NOTEBOOK_PYTHON ?= ../notebook/.venv/bin/python
NOTEBOOK_PYTHON_PATH := $(abspath $(NOTEBOOK_PYTHON))
CRAWLER_TOOL_DIR := crawler
CRAWLER_TOOL_PATH := $(abspath $(CRAWLER_TOOL_DIR))
export DOCKER_BUILDKIT ?= 1
export COMPOSE_DOCKER_CLI_BUILD ?= 1

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@printf "\nSUUMO Source Crawler - Python service commands\n\n"
	@printf "Usage:\n"
	@printf "  make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\nExamples:\n"
	@printf "  make -C .. infra-up-d\n"
	@printf "  make build\n"
	@printf "  make up\n"
	@printf "  make ps\n"
	@printf "  make logs\n"
	@printf "  make python3 main/main.py\n"
	@printf "  make python3-container workdir=/app/crawler args=\"-m scrapy crawl suumo_links\"\n"
	@printf "  make prod-minio-preview path=\"suumo/data/20260723T165050155977Z.json.gz\"\n"
	@printf "  make prod-task-json task_ids=\"123 456\" opts=\"--write-json\"\n"
	@printf "  make telegram-test\n"
	@printf "  make shell\n\n"

.PHONY: config
config: ## Validate and render the docker compose config
	$(COMPOSE) --env-file $(ENV_FILE) config

.PHONY: build
build: ## Build local images
	$(COMPOSE) --env-file $(ENV_FILE) build

.PHONY: pull
pull: ## Pull service images
	$(COMPOSE) --env-file $(ENV_FILE) pull

.PHONY: up
up: ## Start the Python crawler service in foreground using the existing image
	$(COMPOSE) --env-file $(ENV_FILE) up

.PHONY: up-d
up-d: ## Start the Python crawler service in background using the existing image
	$(COMPOSE) --env-file $(ENV_FILE) up -d

.PHONY: up-build
up-build: ## Build then start the Python crawler service in foreground
	$(COMPOSE) --env-file $(ENV_FILE) up --build

.PHONY: up-build-d
up-build-d: ## Build then start the Python crawler service in background
	$(COMPOSE) --env-file $(ENV_FILE) up --build -d

.PHONY: down
down: ## Stop and remove the Python crawler container, keep volumes
	$(COMPOSE) --env-file $(ENV_FILE) down

.PHONY: restart
restart: ## Restart the Python crawler service
	$(COMPOSE) --env-file $(ENV_FILE) restart

.PHONY: ps
ps: ## Show service status
	$(COMPOSE) --env-file $(ENV_FILE) ps

.PHONY: logs
logs: ## Follow Python crawler logs
	$(COMPOSE) --env-file $(ENV_FILE) logs -f python

.PHONY: health
health: ## Show container health status
	@$(COMPOSE) --env-file $(ENV_FILE) ps

.PHONY: shell
shell: ## Open a shell in the python container
	$(COMPOSE) --env-file $(ENV_FILE) exec python sh

.PHONY: python
python: ## Open a Python REPL in the python container
	$(COMPOSE) --env-file $(ENV_FILE) exec python python

.PHONY: python3
python3: ## Run local python3. Use args="..." for options like -m.
	$(PYTHON) $(PYTHON_ARGS)

.PHONY: python3-container
python3-container: ## Run container python. Use args="..." for options like -m.
	$(COMPOSE) --env-file $(ENV_FILE) exec $(CONTAINER_WORKDIR) python python $(PYTHON_ARGS)

.PHONY: minio-preview
minio-preview: ## Preview a MinIO object, optionally pass path="suumo/..." opts="--write-json"
	$(COMPOSE) --env-file $(ENV_FILE) exec -w /app/crawler python python tools/minio_preview.py $(path) $(opts)

.PHONY: prod-minio-preview
prod-minio-preview: ## Preview VPS MinIO object with ../.env.production, pass path="suumo/..." opts="--write-json"
	@test -n "$(path)" || { printf "Usage: make prod-minio-preview path=\"suumo/data/....json.gz\" opts=\"--write-json\"\n"; exit 1; }
	@test -f "$(PRODUCTION_ENV_PATH)" || { printf "Missing %s\n" "$(PRODUCTION_ENV_PATH)"; exit 1; }
	@test -x "$(NOTEBOOK_PYTHON_PATH)" || { printf "Missing executable %s. Run from repo root: uv venv notebook/.venv && uv pip install --python notebook/.venv/bin/python -r notebook/requirements.txt\n" "$(NOTEBOOK_PYTHON_PATH)"; exit 1; }
	@set -eu; \
	cd "$(CRAWLER_TOOL_PATH)"; \
	set -a; . "$(PRODUCTION_ENV_PATH)"; set +a; \
	PYTHONPATH="$(CRAWLER_TOOL_PATH)" "$(NOTEBOOK_PYTHON_PATH)" tools/minio_preview.py "$(path)" $(opts)

.PHONY: prod-task-json
prod-task-json: ## Fetch parser JSON records for VPS task ids, pass task_ids="123 456" opts="--write-json --records-only"
	@test -n "$(task_ids)" || { printf "Usage: make prod-task-json task_ids=\"123 456\" opts=\"--write-json\"\n"; exit 1; }
	@test -f "$(PRODUCTION_ENV_PATH)" || { printf "Missing %s\n" "$(PRODUCTION_ENV_PATH)"; exit 1; }
	@test -x "$(NOTEBOOK_PYTHON_PATH)" || { printf "Missing executable %s. Run from repo root: uv venv notebook/.venv && uv pip install --python notebook/.venv/bin/python -r notebook/requirements.txt\n" "$(NOTEBOOK_PYTHON_PATH)"; exit 1; }
	@set -eu; \
	cd "$(CRAWLER_TOOL_PATH)"; \
	set -a; . "$(PRODUCTION_ENV_PATH)"; set +a; \
	PYTHONPATH="$(CRAWLER_TOOL_PATH)" "$(NOTEBOOK_PYTHON_PATH)" tools/task_json_preview.py $(task_ids) $(opts)

.PHONY: manual-rerun-failed-html
manual-rerun-failed-html: ## Rerun failed crawl_tasks through suumo_html, optionally pass opts="--limit 10"
	$(COMPOSE) --env-file $(ENV_FILE) exec -w /app/crawler python python tools/manual_rerun_failed_html.py $(opts)

.PHONY: telegram-test
telegram-test: ## Send one Telegram test message using ../.env
	$(COMPOSE) --env-file $(ENV_FILE) run --rm python telegram-test $(opts)

# Allow commands like `make python3 main/main.py` where the script path is treated as an argument.
# Use args="..." when arguments start with "-", because make parses those as its own options.
.PHONY: FORCE
%: FORCE
	@:

FORCE:

.PHONY: clean
clean: ## Stop the Python crawler container and remove anonymous containers/networks, keep named volumes
	$(COMPOSE) --env-file $(ENV_FILE) down --remove-orphans

.PHONY: clean-volumes
clean-volumes: ## Stop the Python crawler container and remove named volumes. This deletes local Python cache data.
	$(COMPOSE) --env-file $(ENV_FILE) down --volumes --remove-orphans
