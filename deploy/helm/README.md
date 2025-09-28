# Ansible Log Monitor - OpenShift Deployment

A Helm-based deployment for the Ansible Log Monitor system on OpenShift.

> **Note**: All commands use the current OpenShift project by default. No need to specify `NAMESPACE` unless you want to use a different one.

## Prerequisites

- OpenShift CLI (`oc`) installed and configured
- Helm 3.x installed
- Access to an OpenShift cluster
- MaaS API Token for AI services

## Quick Start

### 1. Install the Application

```bash
# Basic installation (uses current OpenShift project)
make install OPENAI_API_TOKEN=your-token-here

# With custom AI model settings
make install NAMESPACE=ansible-logs-monitor \
  OPENAI_API_TOKEN=your-token-here \
  OPENAI_MODEL=llama-4-scout-17b-16e-w4a16 \
  OPENAI_TEMPERATURE=0.7

# Specify a custom namespace (optional)
make install NAMESPACE=ansible-logs-monitor OPENAI_API_TOKEN=your-token-here
```

### 2. Access the Services

```bash
# Forward UI to localhost:7860 (uses current OpenShift project)
make port-forward-ui

# Forward Backend API to localhost:8000
make port-forward-backend

# Forward Annotation Interface to localhost:7861
make port-forward-annotation

# Forward Grafana to localhost:3000
make port-forward-grafana

# Specify a custom namespace (optional)
make port-forward-ui NAMESPACE=ansible-logs-monitor
```

### 3. Uninstall

```bash
# Uninstall from current OpenShift project
make uninstall

# Uninstall from specific namespace (optional)
make uninstall NAMESPACE=ansible-logs-monitor
```

## Available Commands

| Command | Description | Required Parameters |
|---------|-------------|-------------------|
| `make install` | Deploy the application | `OPENAI_API_TOKEN` |
| `make uninstall` | Remove the application | None |
| `make namespace` | Create/switch to namespace | None |
| `make port-forward-ui` | Forward UI service | None |
| `make port-forward-backend` | Forward Backend service | None |
| `make port-forward-annotation` | Forward Annotation Interface | None |
| `make port-forward-grafana` | Forward Grafana | None |
| `make help` | Show all available commands | None |

**Note**: All commands use the current OpenShift project by default. Use `NAMESPACE=your-namespace` to override.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_TOKEN` | *Required* | MaaS API Token for AI services |
| `OPENAI_API_ENDPOINT` | `https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1` | AI API endpoint |
| `OPENAI_MODEL` | `llama-4-scout-17b-16e-w4a16` | AI model to use |
| `OPENAI_TEMPERATURE` | `0.7` | AI temperature setting |

### Examples

#### Basic Installation
```bash
# Uses current OpenShift project
make install OPENAI_API_TOKEN=abc123

# Specify custom namespace
make install NAMESPACE=my-ansible-logs OPENAI_API_TOKEN=abc123
```

#### Custom Configuration
```bash
# Uses current OpenShift project with custom settings
make install \
  OPENAI_API_TOKEN=abc123 \
  OPENAI_MODEL=custom-model \
  OPENAI_TEMPERATURE=0.5
