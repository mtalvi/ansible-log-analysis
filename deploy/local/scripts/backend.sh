#!/bin/bash
# set -e

# Function to cleanup background processes on exit
# cleanup() {
#     echo ""
#     echo "🛑 Stopping Backend service..."
#     if [ ! -z "$BACKEND_PID" ]; then
#         kill $BACKEND_PID 2>/dev/null
#         echo "   ✓ Backend stopped"
#     fi
#     echo "👋 Backend service stopped"
#     exit 0
# }

# # Set up signal handlers
# trap cleanup SIGINT SIGTERM

# echo "⚙️  Starting Backend (FastAPI)..."

# Load environment variables
if [ -f ../../.env ]; then
    source ../../.env
    export DATABASE_URL
    export BACKEND_URL
    export OPENAI_API_TOKEN
    export OPENAI_API_ENDPOINT  
    export OPENAI_MODEL
    export LANGSMITH_TRACING
    export LANGSMITH_API_KEY
    export LANGSMITH_PROJECT
fi

# Start backend in background
( cd ../.. && uv run uvicorn src.alm.main_fastapi:app --reload ) &
BACKEND_PID=$!

# Keep the script running and wait for interrupt
# wait