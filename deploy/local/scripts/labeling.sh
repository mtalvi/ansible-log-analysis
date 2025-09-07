#!/bin/bash
# set -e

# # Function to cleanup background processes on exit
# cleanup() {
#     echo ""
#     echo "🛑 Stopping Labeling UI service..."
#     if [ ! -z "$LABELING_PID" ]; then
#         kill $LABELING_PID 2>/dev/null
#         echo "   ✓ Labeling UI stopped"
#     fi
#     echo "👋 Labeling UI service stopped"
#     exit 0
# }

# # Set up signal handlers
# trap cleanup SIGINT SIGTERM

# echo "🏷️  Starting Labeling UI (Gradio)..."

# Start labeling UI in background
( cd ../.. && uv run gradio labeling_interface/app.py ) & LABELING_PID=$!

# Keep the script running and wait for interrupt
# wait