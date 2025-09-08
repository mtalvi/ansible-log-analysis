.PHONY: deploy start stop status help postgres backend ui labeling health logs restart clean
.DEFAULT_GOAL := help

deploy: start ## Deploy all services (alias for start)

help: ## Show this help message
	@echo "🚀 Ansible Log Monitor - Local Deployment"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
	@echo ""


start: stop ## 🚀 Start all services locally
	@echo "🚀 Starting local deployment of Ansible Log Monitor..."
	@echo "🔌 Cleaning up any existing processes..."
	@$(MAKE) -s postgres
	@echo "   Waiting for PostgreSQL to be ready..."
	@sleep 5
	@$(MAKE) -s backend
	@$(MAKE) -s ui
	@$(MAKE) -s labeling
	@echo ""
	@echo "🎉 All services are running!"
	@$(MAKE) -s status
	@echo ""
	@echo "Press Ctrl+C to stop all services, or run 'make stop'"
	@bash -c 'trap "exit" SIGINT SIGTERM; while true; do sleep 1; done'

postgres: ## 📊 Start PostgreSQL database
	@echo "   Starting PostgreSQL database..."
	@docker-compose -f compose.yaml up -d postgres
	@sleep 3

backend: ## ⚙️ Start Backend (FastAPI)
	@echo "   Starting Backend API..."
	@( cd ../.. && uv run uvicorn src.alm.main_fastapi:app --reload ) &
	@sleep 3

ui: ## 🖥️ Start UI (Gradio)
	@echo "   Starting UI Interface..."
	@( cd ../../ui && uv run gradio app.py ) &
	@sleep 3

labeling: ## 🏷️ Start Labeling UI (Gradio)  
	@echo "   Starting Labeling UI..."
	@( cd ../.. && uv run gradio labeling_interface/app.py ) &
	@sleep 3


stop: ## 🛑 Stop all services
	@echo "🛑 Stopping all services..."
	@$(MAKE) -s stop-postgres
	@$(MAKE) -s kill-ports
	@echo "👋 All services stopped"

stop-postgres: ## 🛑 Stop PostgreSQL database
	@docker-compose -f compose.yaml down postgres
	@echo "   ✓ PostgreSQL stopped"

kill-ports: ## 🔌 Kill processes using required ports
	@fuser -k 7860/tcp || true
	@echo "   ✓ UI 7860 killed"
	@fuser -k 7861/tcp || true
	@echo "   ✓ Labeling 7861 killed"
	@fuser -k 8000/tcp || true
	@echo "   ✓ Backend 8000 killed"

status: ## 📊 Show status of all services
	@echo "📊 Service Status:"
	@echo "   📊 PostgreSQL: $(shell docker-compose ps -q postgres >/dev/null 2>&1 && echo 'Running' || echo 'Stopped') - localhost:5432"
	@if lsof -i :8000 >/dev/null 2>&1; then \
		echo "   ⚙️  Backend API: Running - http://localhost:8000"; \
	else \
		echo "   ⚙️  Backend API: Stopped - http://localhost:8000"; \
	fi
	@if lsof -i :7860 >/dev/null 2>&1; then \
		echo "   🖥️  UI Interface: Running - http://localhost:7860"; \
	else \
		echo "   🖥️  UI Interface: Stopped - http://localhost:7860"; \
	fi
	@if lsof -i :7861 >/dev/null 2>&1; then \
		echo "   🏷️  Labeling UI: Running - http://localhost:7861"; \
	else \
		echo "   🏷️  Labeling UI: Stopped - http://localhost:7861"; \
	fi

run-whole-training-pipeline: ## 🔍 Run whole training pipeline
	@echo "🔍 Running whole training pipeline..."
	@( cd ../.. && uv run init_pipeline.py )

health: ## 🔍 Check health of running services
	@echo "🔍 Health Checks:"
	@if curl -s http://localhost:8000/health >/dev/null 2>&1; then \
		echo "   ⚙️  Backend http://localhost:8000: Healthy"; \
	else \
		echo "   ⚙️  Backend http://localhost:8000: Unhealthy"; \
	fi
	@if curl -s http://localhost:7860 >/dev/null 2>&1; then \
		echo "   🖥️  UI http://localhost:7860: Healthy"; \
	else \
		echo "   🖥️  UI http://localhost:7860: Unhealthy"; \
	fi
	@if curl -s http://localhost:7861 >/dev/null 2>&1; then \
		echo "   🏷️  Labeling UI http://localhost:7861: Healthy"; \
	else \
		echo "   🏷️  Labeling UI http://localhost:7861: Unhealthy"; \
	fi

restart: stop start ## 🔄 Restart all services

clean: ## 🧹 Clean PID files and logs
	@echo "🧹 Cleaning up PID files and logs..."
	@echo "   ✓ Cleanup completed"
