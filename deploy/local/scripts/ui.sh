#!/bin/bash
# set -e

# # Function to cleanup background processes on exit
# cleanup() {
#     echo ""
#     echo "🛑 Stopping UI service..."
#     if [ ! -z "$UI_PID" ]; then
#         kill $UI_PID 2>/dev/null
#         echo "   ✓ UI stopped"
#     fi
#     echo "👋 UI service stopped"
#     exit 0
# }

# # Set up signal handlers
# trap cleanup SIGINT SIGTERM

# echo "🖥️  Starting UI (Gradio)..."

# Start UI in background
( cd ../../ui && uv run gradio app.py ) & UI_PID=$!

# Keep the script running and wait for interrupt
# wait