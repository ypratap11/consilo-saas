# FlowIQ Makefile - Common Commands

.PHONY: help setup start stop restart logs test clean deploy seed

help:  ## Show this help message
	@echo "FlowIQ SaaS - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Initial setup - copy .env and generate key
	@echo "Setting up FlowIQ..."
	@cp -n .env.example .env || true
	@echo "✅ Created .env file"
	@echo ""
	@echo "⚠️  Generate encryption key and add to .env:"
	@python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
	@echo ""

start:  ## Start all services
	@echo "Starting FlowIQ services..."
	docker-compose up -d
	@echo "✅ Services started"
	@echo "API: http://localhost:8080"
	@echo "Docs: http://localhost:8080/docs"

stop:  ## Stop all services
	@echo "Stopping FlowIQ services..."
	docker-compose down
	@echo "✅ Services stopped"

restart:  ## Restart all services
	@echo "Restarting FlowIQ services..."
	docker-compose down
	docker-compose up -d
	@echo "✅ Services restarted"

logs:  ## View backend logs
	docker-compose logs -f backend

logs-db:  ## View database logs
	docker-compose logs -f postgres

logs-all:  ## View all logs
	docker-compose logs -f

test:  ## Run local test suite
	python test_local.py

test-health:  ## Quick health check
	@curl -s http://localhost:8080/health | python -m json.tool

seed:  ## Seed database with subscription plans
	docker-compose exec backend python seed.py

clean:  ## Remove all containers and volumes (DESTRUCTIVE)
	@echo "⚠️  This will delete all data. Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	docker-compose down -v
	@echo "✅ Cleaned up"

rebuild:  ## Rebuild and restart (after code changes)
	docker-compose up -d --build

shell:  ## Open shell in backend container
	docker-compose exec backend /bin/bash

db-shell:  ## Open PostgreSQL shell
	docker-compose exec postgres psql -U flowiq -d flowiq

db-backup:  ## Backup database
	@echo "Backing up database..."
	docker-compose exec -T postgres pg_dump -U flowiq flowiq > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup complete"

db-restore:  ## Restore database from backup (usage: make db-restore FILE=backup.sql)
	@echo "Restoring database from $(FILE)..."
	docker-compose exec -T postgres psql -U flowiq -d flowiq < $(FILE)
	@echo "✅ Restore complete"

install-dev:  ## Install development dependencies
	pip install -r backend/requirements.txt
	pip install pytest httpx black flake8

format:  ## Format code with black
	black backend/app/

lint:  ## Lint code
	flake8 backend/app/

docs:  ## Generate API documentation
	@echo "Opening API docs..."
	@open http://localhost:8080/docs || xdg-open http://localhost:8080/docs || echo "Visit: http://localhost:8080/docs"

status:  ## Show service status
	@echo "FlowIQ Service Status:"
	@docker-compose ps

api-url:  ## Show API URLs
	@echo "Local URLs:"
	@echo "  API: http://localhost:8080"
	@echo "  Docs: http://localhost:8080/docs"
	@echo "  Health: http://localhost:8080/health"

# Production commands

deploy-check:  ## Pre-deployment checklist
	@echo "Pre-Deployment Checklist:"
	@echo "  [ ] .env has production DATABASE_URL"
	@echo "  [ ] New ENCRYPTION_KEY generated"
	@echo "  [ ] GitHub repo created and pushed"
	@echo "  [ ] DigitalOcean PostgreSQL created"
	@echo "  [ ] App Platform configured"
	@echo ""
	@echo "Ready to deploy? See DEPLOYMENT.md"

# Week 1 checklist

week1:  ## Show Week 1 checklist
	@cat WEEK_1_CHECKLIST.md

quick:  ## Show quick start guide
	@cat QUICKSTART.md
