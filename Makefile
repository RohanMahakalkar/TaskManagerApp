.PHONY: help build up down logs rebuild clean dev prod test

help:
	@echo "FastAPI Docker Commands"
	@echo "======================="
	@echo "make dev         - Run development environment with hot reload"
	@echo "make prod        - Run production environment"
	@echo "make build       - Build all containers"
	@echo "make up          - Start production containers"
	@echo "make down        - Stop all containers"
	@echo "make rebuild     - Rebuild and restart production containers"
	@echo "make dev-rebuild - Rebuild and restart dev containers"
	@echo "make logs        - View production logs"
	@echo "make dev-logs    - View development logs"
	@echo "make test        - Run tests in production containers"
	@echo "make ps          - Show running containers"
	@echo "make clean       - Remove all containers and volumes"
	@echo "make shell       - Open shell in running app container"

# Development environment
dev:
	docker-compose -f docker-compose.dev.yml up -d

dev-rebuild:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up -d --build

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f app

dev-stop:
	docker-compose -f docker-compose.dev.yml down

# Production environment
prod:
	docker-compose up -d

build:
	docker-compose build

rebuild: down
	docker-compose up -d --build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# Testing
test:
	docker-compose exec app pytest -v

# Database
db-shell:
	docker-compose exec mongo mongosh

redis-shell:
	docker-compose exec redis redis-cli

# Application shell
shell:
	docker-compose exec app /bin/bash

app-shell-dev:
	docker-compose -f docker-compose.dev.yml exec app /bin/bash

# Container management
ps:
	docker-compose ps

ps-dev:
	docker-compose -f docker-compose.dev.yml ps

# Cleanup
clean: down
	docker volume prune -f
	docker system prune -f

clean-all: down
	docker volume prune -af
	docker system prune -af

# Development utilities
requirements:
	docker-compose -f docker-compose.dev.yml exec app pip freeze > requirements.txt

install-package:
	@read -p "Enter package name: " pkg; \
	docker-compose -f docker-compose.dev.yml exec app pip install $$pkg

# Status check
status:
	@echo "=== Production Environment ===" && \
	docker-compose ps && \
	echo "\n=== Container Health ===" && \
	docker ps --format "table {{.Names}}\t{{.Status}}"
