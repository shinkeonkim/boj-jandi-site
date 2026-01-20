FROM ghcr.io/astral-sh/uv:latest AS uv

FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install uv
COPY --from=uv /uv /uvx /bin/

# Copy the project's dependency files
COPY pyproject.toml uv.lock ./

# Install the project's dependencies using the lockfile and settings
# --no-dev to avoid installing dev dependencies (if any)
RUN uv sync --frozen --no-dev

COPY app /app/app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

CMD ["fastapi", "run", "app/main.py", "--port", "8080", "--host", "0.0.0.0"]
