# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first (better layer caching)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen || uv sync --no-dev

COPY . .

# Cloud Run injects $PORT (defaults to 8080); fall back to 8000 for local/compose.
# Run the pre-built venv's uvicorn directly — NOT `uv run`, which re-syncs (and reinstalls dev deps)
# at startup, slowing boot enough to fail Cloud Run's startup health check. `app` stays importable
# via the working directory.
EXPOSE 8000
CMD ["sh", "-c", ".venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
