# ============================================================================
# Builder Stage - Install dependencies
# ============================================================================
FROM registry.access.redhat.com/ubi8/python-312 AS builder

USER root

# Install uv pointing to the uv image and coping from there
# /uv and /uvx are the source files copied from the uv image
# /bin is the destination
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (for optimal layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (not the project itself yet)
# Uses BuildKit cache mount for persistent package caching across builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code and install project in production mode (not editable)
COPY src/ ./src/
COPY data/logs/failed/ ./data/logs/failed/
COPY init_pipeline.py ./

# For debug
# COPY examples/ ./examples/

# Install the project itself (production mode, not editable)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# ============================================================================
# Runtime Stage
# ============================================================================
FROM registry.access.redhat.com/ubi8/python-312

USER root

WORKDIR /app

# Copy installed dependencies and project from builder
COPY --from=builder /app /app

# Set virtual environment and Hugging Face cache
ENV VIRTUAL_ENV=.venv \
    PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/hf_cache

# In OpenShift, random UID is always group 0, grant group 0 access to the directories
RUN mkdir -p /hf_cache && \
    chgrp -R 0 /app /hf_cache && \
    chmod -R g=u /app /hf_cache

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
ENTRYPOINT ["uvicorn", "alm.main_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
