SHELL := /bin/sh

COMPOSE := docker compose
ENV_FILE := ../.env
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

.PHONY: clean
clean: ## Stop the Python crawler container and remove anonymous containers/networks, keep named volumes
	$(COMPOSE) --env-file $(ENV_FILE) down --remove-orphans

.PHONY: clean-volumes
clean-volumes: ## Stop the Python crawler container and remove named volumes. This deletes local Python cache data.
	$(COMPOSE) --env-file $(ENV_FILE) down --volumes --remove-orphans
