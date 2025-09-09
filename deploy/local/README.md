# Local Deployment

Quick setup for running Ansible Log Monitor locally with PostgreSQL, FastAPI backend, and Gradio UIs.

## Quick Start

```bash
make start    # Start all services
make status   # Check service status
make health   # Health check endpoints
make stop     # Stop all services
```

## Services

- **PostgreSQL**: Database (localhost:5432)
- **Backend API**: FastAPI server (http://localhost:8000)
- **UI Interface**: Main Gradio UI (http://localhost:7860)
- **Annotation UI**: Annotation interface (http://localhost:7861)

## Requirements

- docker-compose (for PostgreSQL)
- uv (Python package manager)
- Required ports: 5432, 7860, 7861, 8000

Run `make help` for all available commands.
