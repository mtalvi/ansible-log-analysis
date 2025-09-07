.PHONY: deploy start stop status help postgres backend ui labeling health
.DEFAULT_GOAL := help

ifneq (,$(wildcard ../../.env))
# ifneq (,$(filter local,$(MAKECMDGOALS)))
include ../../.env
# endif
endif

# PID files for process management
BACKEND_PID_FILE := .backend.pid
UI_PID_FILE := .ui.pid  
LABELING_PID_FILE := .labeling.pid

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
	# @$(MAKE) -s postgres
	@sleep 3
	@$(MAKE) -s backend
	@sleep 1
	@$(MAKE) -s ui
	@$(MAKE) -s labeling
	@echo ""
	@echo "🎉 All services are running!"
	@$(MAKE) -s status
	@echo ""
	@echo "Press Ctrl+C to stop all services, or run 'make stop'"

postgres: ## 📊 Start PostgreSQL database
	scripts/postgres.sh

backend: ## ⚙️ Start Backend (FastAPI)
	scripts/backend.sh

ui: ## 🖥️ Start UI (Gradio)
	scripts/ui.sh

labeling: ## 🏷️ Start Labeling UI (Gradio)  
	scripts/labeling.sh

stop: ## 🛑 Stop all services
	@echo "🛑 Stopping all services..."
	@if [ -f $(BACKEND_PID_FILE) ]; then \
		if kill -0 `cat $(BACKEND_PID_FILE)` 2>/dev/null; then \
			kill `cat $(BACKEND_PID_FILE)` 2>/dev/null; \
			echo "   ✓ Backend stopped"; \
		fi; \
		rm -f $(BACKEND_PID_FILE); \
	fi
	@if [ -f $(UI_PID_FILE) ]; then \
		if kill -0 `cat $(UI_PID_FILE)` 2>/dev/null; then \
			kill `cat $(UI_PID_FILE)` 2>/dev/null; \
			echo "   ✓ UI stopped"; \
		fi; \
		rm -f $(UI_PID_FILE); \
	fi
	@if [ -f $(LABELING_PID_FILE) ]; then \
		if kill -0 `cat $(LABELING_PID_FILE)` 2>/dev/null; then \
			kill `cat $(LABELING_PID_FILE)` 2>/dev/null; \
			echo "   ✓ Labeling UI stopped"; \
		fi; \
		rm -f $(LABELING_PID_FILE); \
	fi
	# docker-compose down
	@echo "   ✓ PostgreSQL stopped"
	@$(MAKE) -s kill-ports
	@echo "👋 All services stopped"

kill-ports: ## 🔌 Kill processes using required ports
	@fuser -k 7860/tcp 2>/dev/null || true
	@fuser -k 7861/tcp 2>/dev/null || true
	@fuser -k 8000/tcp 2>/dev/null || true

status: ## 📊 Show status of all services
	@echo "📊 Service Status:"
	@echo "   📊 PostgreSQL: $(shell docker-compose ps -q postgres >/dev/null 2>&1 && echo 'Running' || echo 'Stopped') - localhost:5432"
	@if [ -f $(BACKEND_PID_FILE) ] && kill -0 `cat $(BACKEND_PID_FILE)` 2>/dev/null; then \
		echo "   ⚙️  Backend API: Running - http://localhost:8000"; \
	else \
		echo "   ⚙️  Backend API: Stopped - http://localhost:8000"; \
	fi
	@if [ -f $(UI_PID_FILE) ] && kill -0 `cat $(UI_PID_FILE)` 2>/dev/null; then \
		echo "   🖥️  UI Interface: Running - http://localhost:7860"; \
	else \
		echo "   🖥️  UI Interface: Stopped - http://localhost:7860"; \
	fi
	@if [ -f $(LABELING_PID_FILE) ] && kill -0 `cat $(LABELING_PID_FILE)` 2>/dev/null; then \
		echo "   🏷️  Labeling UI: Running - http://localhost:7861"; \
	else \
		echo "   🏷️  Labeling UI: Stopped - http://localhost:7861"; \
	fi

health: ## 🔍 Check health of running services
	@echo "🔍 Health Checks:"
	@if curl -s http://localhost:8000/health >/dev/null 2>&1; then \
		echo "   ⚙️  Backend: Healthy"; \
	else \
		echo "   ⚙️  Backend: Unhealthy"; \
	fi
	@if curl -s http://localhost:7860 >/dev/null 2>&1; then \
		echo "   🖥️  UI: Healthy"; \
	else \
		echo "   🖥️  UI: Unhealthy"; \
	fi
	@if curl -s http://localhost:7861 >/dev/null 2>&1; then \
		echo "   🏷️  Labeling UI: Healthy"; \
	else \
		echo "   🏷️  Labeling UI: Unhealthy"; \
	fi

logs: ## 📝 Show logs for all services
	@echo "📝 Service Logs:"
	@echo "=== Backend Logs ==="
	@tail -20 .backend.log 2>/dev/null || echo "No backend logs found"
	@echo "=== UI Logs ===" 
	@tail -20 .ui.log 2>/dev/null || echo "No UI logs found"
	@echo "=== Labeling UI Logs ==="
	@tail -20 .labeling.log 2>/dev/null || echo "No labeling UI logs found"
	@echo "=== PostgreSQL Logs ==="
	@docker-compose logs --tail=20 postgres 2>/dev/null || echo "No PostgreSQL logs found"

restart: stop start ## 🔄 Restart all services
