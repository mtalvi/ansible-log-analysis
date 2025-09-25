FROM registry.access.redhat.com/ubi8/python-312

USER root

# Install uv pointing to the uv image and coping from there
# /uv and /uvx are the source files copied from the uv image
# /bin is the destination
COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
# COPY uv.lock ./

# Install dependencies
RUN uv sync --no-dev
ENV VIRTUAL_ENV=.venv
ENV PATH=".venv/bin:$PATH"

# Copy source code
COPY src/ ./src/
COPY init_pipeline.py .
COPY data/ ./data/

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
ENTRYPOINT ["python", "-m", "uvicorn", "src.alm.main_fastapi:app", "--host", "0.0.0.0", "--port", "8000"] 