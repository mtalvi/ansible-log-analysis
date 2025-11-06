#!/bin/bash
# Entrypoint script for backend service
set -e

# Setup data directory structure (symlinks, etc.)
if [ -f /app/setup_data_dirs.sh ]; then
    /app/setup_data_dirs.sh
fi

# Execute the main command (uvicorn or whatever is passed)
exec "$@"

