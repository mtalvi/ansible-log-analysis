# Makefile for Ansible Log Monitor Deployment
# Replaces the original deploy.sh script with additional uninstall functionality

MAKEFLAGS += --no-print-directory

# Default values
NAMESPACE ?= $(shell oc project -q 2>/dev/null || echo "default")
OPENAI_API_ENDPOINT ?= https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1
OPENAI_MODEL ?= llama-4-scout-17b-16e-w4a16
OPENAI_TEMPERATURE ?= 0.7
ANSIBLE_LOG_MONITOR_CHART := ansible-log-monitor

# Parameter validation functions
define check_namespace
	@echo "Using namespace: $(NAMESPACE)"
endef

# define check_required_params
# 	@if [ -z "$(OPENAI_API_TOKEN)" ]; then \
# 		echo "Error: OPENAI_API_TOKEN is required for installation"; \
# 		echo "Usage: make $@ OPENAI_API_TOKEN=your-token"; \
# 		exit 1; \
# 	fi
# 	@echo "Using namespace: $(NAMESPACE)"
# endef


env_args = \
	-f ansible-log-monitor/global-values.yaml \
	-f ansible-log-monitor/values.yaml

# Default target
.PHONY: help
help:
	@echo "Ansible Log Monitor - OpenShift Deployment"
	@echo "=========================================="
	@echo ""
	@echo "Available Commands:"
	@echo "  install                    Deploy the application (requires OPENAI_API_TOKEN)"
	@echo "  uninstall                  Remove the application"
	@echo "  namespace                  Create/switch to namespace"
	@echo "  port-forward-ui           Forward UI service to localhost:7860"
	@echo "  port-forward-backend      Forward Backend service to localhost:8000"
	@echo "  port-forward-annotation   Forward Annotation Interface to localhost:7861"
	@echo "  port-forward-grafana      Forward Grafana to localhost:3000"
	@echo ""
	@echo "Usage Examples:"
	@echo "  make install OPENAI_API_TOKEN=your-token-here"
	@echo "  make install NAMESPACE=ansible-logs OPENAI_API_TOKEN=your-token-here"
	@echo "  make uninstall"
	@echo "  make port-forward-ui"
	@echo ""
	@echo "Configuration Variables:"
	@echo "  NAMESPACE                  OpenShift namespace (default: current project)"
	@echo "  OPENAI_API_TOKEN          MaaS API Token (required for install)"
	@echo "  OPENAI_API_ENDPOINT       AI API endpoint (default: llama-4-scout endpoint)"
	@echo "  OPENAI_MODEL              AI model to use (default: llama-4-scout-17b-16e-w4a16)"
	@echo "  OPENAI_TEMPERATURE        AI temperature setting (default: 0.7)"
	@echo ""
	@echo "Note: All commands use the current OpenShift project by default."
	@echo "      Use NAMESPACE=your-namespace to override."



# Create namespace/project and deploy (NAMESPACE optional, defaults to current project)
.PHONY: namespace
namespace:
	$(call check_namespace)
	@echo "Setting up project $(NAMESPACE)..."
	@oc new-project $(NAMESPACE) 2>/dev/null || oc project $(NAMESPACE) 2>/dev/null || true
	@oc label namespace $(NAMESPACE) app=ansible-log-monitor --overwrite
	@echo "Project $(NAMESPACE) ready"

# Install the application (NAMESPACE optional, defaults to current project)
.PHONY: install
install: namespace
	# $(call check_required_params)
	@echo "Installing Ansible Log Monitor in namespace $(NAMESPACE)..."
	@oc project $(NAMESPACE)
	@helm install alm ./ansible-log-monitor -n $(NAMESPACE) $(env_args)
	@echo "Ansible Log Monitor installed"

# Uninstall the deployment and clean up (NAMESPACE optional, defaults to current project)
.PHONY: uninstall
uninstall: 
	$(call check_namespace)
	@echo "Uninstalling Ansible Log Monitor from namespace $(NAMESPACE)..."
	@helm uninstall alm -n $(NAMESPACE)
	@echo "Ansible Log Monitor uninstalled"

# Upgrade 
.PHONY: upgrade
upgrade:
	$(call check_namespace)
	@echo "Upgrading Ansible Log Monitor in namespace $(NAMESPACE)..."
	@helm upgrade alm ./ansible-log-monitor -n $(NAMESPACE) $(env_args)
	@echo "Ansible Log Monitor upgraded"

# Port forwarding helpers (NAMESPACE optional, defaults to current project)
.PHONY: port-forward-ui
port-forward-ui:
	$(call check_namespace)
	@echo "🔗 Forwarding UI service to localhost:7860..."
	@oc port-forward -n $(NAMESPACE) svc/ui 7860:7860

.PHONY: port-forward-backend
port-forward-backend:
	$(call check_namespace)
	@echo "🔗 Forwarding Backend service to localhost:8000..."
	@oc port-forward -n $(NAMESPACE) svc/backend 8000:8000

.PHONY: port-forward-annotation
port-forward-annotation:
	$(call check_namespace)
	@echo "🔗 Forwarding Annotation Interface to localhost:7861..."
	@oc port-forward -n $(NAMESPACE) svc/annotation-interface 7861:7861

.PHONY: port-forward-grafana
port-forward-grafana:
	$(call check_namespace)
	@echo "🔗 Forwarding Grafana to localhost:3000..."
	@oc port-forward -n $(NAMESPACE) svc/grafana 3000:3000