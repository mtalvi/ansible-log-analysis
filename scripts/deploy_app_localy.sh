#!/bin/bash

# Deploy Ansible Log Monitor locally - all 3 components
echo "🚀 Starting local deployment of Ansible Log Monitor..."
echo "🔌 Killing any process using port 7860..."
fuser -k 7860/tcp 2>/dev/null
echo "🔌 Killing any process using port 7861..."
fuser -k 7861/tcp 2>/dev/null

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   ✓ Backend stopped"
    fi
    if [ ! -z "$UI_PID" ]; then
        kill $UI_PID 2>/dev/null  
        echo "   ✓ UI stopped"
    fi
    if [ ! -z "$LABELING_UI_PID" ]; then
        kill $LABELING_UI_PID 2>/dev/null
        echo "   ✓ Labeling UI stopped"
    fi
    docker-compose down postgres 2>/dev/null
    echo "   ✓ PostgreSQL stopped"
    echo "👋 All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# 1. Start PostgreSQL database
echo "📊 Starting PostgreSQL database..."
docker-compose up -d postgres
if [ $? -eq 0 ]; then
    echo "   ✓ PostgreSQL started on port 5432"
else
    echo "   ❌ Failed to start PostgreSQL"
    exit 1
fi

# Wait for PostgreSQL to be healthy
echo "   ⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# 2. Start Backend (FastAPI)
echo "⚙️  Starting Backend (FastAPI)..."
uv run uvicorn src.alm.main_fastapi:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 1
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "   ✓ Backend started on http://localhost:8000"
else
    echo "   ❌ Failed to start Backend"
    cleanup
fi

# 3. Start UI (Gradio)
echo "🖥️  Starting UI (Gradio)..."
cd ui && uv run gradio app.py &
UI_PID=$!
ls | echo
# cd ..
sleep 1
if kill -0 $UI_PID 2>/dev/null; then
    echo "   ✓ UI started on http://localhost:7860"
else
    echo "   ❌ Failed to start UI"
    cleanup
fi

# 4. Start Labeling UI (Gradio)
echo "🏷️  Starting Labeling UI (Gradio)..."
uv run gradio labeling_interface/app.py &
LABELING_UI_PID=$!
sleep 1
if kill -0 $LABELING_UI_PID 2>/dev/null; then
    echo "   ✓ Labeling UI started on http://localhost:7861"
else
    echo "   ❌ Failed to start Labeling UI"
    cleanup
fi

echo ""
echo "🎉 All services are running!"
echo "   📊 PostgreSQL: localhost:5432"
echo "   ⚙️  Backend API: http://localhost:8000"
echo "   🖥️  UI Interface: http://localhost:7860"
echo "   🏷️  Labeling UI: http://localhost:7861"
echo ""
echo "📋 Health checks:"
echo "   Backend: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running and wait for interrupt
wait