# Local Deployment

Make sure you have updated the environment variable as defined here: [Local deployment](../../README.md#deploy-locally)

## Available Operations

### Most Used Commands
| Command | Description |
|---------|-------------|
| `make start` | Start all services (PostgreSQL, Backend API, UI, Annotation UI) |
| `make stop` | Stop all services and clean up |
| `make run-whole-training-pipeline` | Execute the complete training pipeline |


### Other Commands
| Command | Description |
|---------|-------------|
| `make help` | Show help message with all available targets |
| `make deploy` | Deploy all services (alias for start) |
| `make postgres` | Start PostgreSQL database only |
| `make backend` | Start Backend API (FastAPI) only |
| `make ui` | Start UI Interface (Gradio) only |
| `make annotation` | Start Annotation UI (Gradio) only |
| `make stop-postgres` | Stop PostgreSQL database only |
| `make kill-ports` | Kill processes using required ports (7860, 7861, 8000) |
| `make status` | Show running status of all services |
| `make health` | Check health endpoints of running services |
| `make restart` | Restart all services |
| `make clean` | Clean PID files and logs |
