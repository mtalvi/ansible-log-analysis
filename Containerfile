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

# Set Hugging Face cache directory
ENV HF_HOME=/hf_cache

RUN  mkdir -p /hf_cache && \
    chmod -R 777 /hf_cache && \
    chmod -R +r .

# Copy source code
COPY src/ ./src/
COPY data/ ./data/
COPY init_pipeline.py .

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
ENTRYPOINT ["uvicorn", "src.alm.main_fastapi:app", "--host", "0.0.0.0", "--port", "8000"] 