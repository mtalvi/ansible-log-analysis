#!/bin/bash
# Setup script to handle data directory structure with PVC mounted at different location
set -e

PVC_MOUNT="/mnt/rag-data"
APP_DATA="/app/data"

echo "Setting up data directory structure..."

# Create necessary directories in PVC if they don't exist
mkdir -p "${PVC_MOUNT}/knowledge_base"
mkdir -p "${PVC_MOUNT}/logs"  # For future use if needed

# Copy knowledge_base PDFs from image to PVC if PVC is empty
if [ ! "$(ls -A ${PVC_MOUNT}/knowledge_base/*.pdf 2>/dev/null)" ]; then
    echo "Copying knowledge_base PDFs from image to PVC..."
    if [ -d "${APP_DATA}/knowledge_base" ] && [ "$(ls -A ${APP_DATA}/knowledge_base/*.pdf 2>/dev/null)" ]; then
        cp -v ${APP_DATA}/knowledge_base/*.pdf ${PVC_MOUNT}/knowledge_base/ || true
        echo "✓ Copied knowledge_base PDFs to PVC"
    fi
fi

# Ensure /app/data directory exists
mkdir -p "${APP_DATA}"

# Create symlinks for persistent data (RAG index and knowledge_base)
# Remove existing directories/files if they exist and are not symlinks
if [ -d "${APP_DATA}/knowledge_base" ] && [ ! -L "${APP_DATA}/knowledge_base" ]; then
    rm -rf "${APP_DATA}/knowledge_base"
fi
if [ -f "${APP_DATA}/ansible_errors.index" ] && [ ! -L "${APP_DATA}/ansible_errors.index" ]; then
    rm -f "${APP_DATA}/ansible_errors.index"
fi
if [ -f "${APP_DATA}/error_metadata.pkl" ] && [ ! -L "${APP_DATA}/error_metadata.pkl" ]; then
    rm -f "${APP_DATA}/error_metadata.pkl"
fi

# Create symlinks to PVC for persistent data
ln -sfn "${PVC_MOUNT}/knowledge_base" "${APP_DATA}/knowledge_base"

# Create symlinks for index files (symlinks work even if target doesn't exist yet)
# When code writes to /app/data/ansible_errors.index, it will write to the PVC via symlink
ln -sfn "${PVC_MOUNT}/ansible_errors.index" "${APP_DATA}/ansible_errors.index"
ln -sfn "${PVC_MOUNT}/error_metadata.pkl" "${APP_DATA}/error_metadata.pkl"

# Ensure logs/failed directory exists (from image, not persisted)
mkdir -p "${APP_DATA}/logs/failed"

echo "✓ Data directory structure setup complete"
echo "  PVC mount: ${PVC_MOUNT}"
echo "  App data: ${APP_DATA}"
echo "  Knowledge base: ${APP_DATA}/knowledge_base -> ${PVC_MOUNT}/knowledge_base"

