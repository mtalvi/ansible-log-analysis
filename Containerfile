FROM registry.access.redhat.com/ubi8/python-312

# Install uv pointing to the uv image and coping from there
# /uv and /uvx are the source files copied from the uv image
# /bin is the destination
COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
# RUN uv sync --frozen --no-dev
RUN uv pip install -r pyproject.toml

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "python", "-m", "uvicorn", "alm.main_fastapi:app", "--host", "0.0.0.0", "--port", "8000"] 