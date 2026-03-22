FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# UV_COMPILE_BYTECODE=1: Compiles all .py files to .pyc upon installation to speed up first-time startup.
# UV_LINK_MODE=copy: Ensures uv copies library files into .venv instead of hardlinking, making the venv portable for multi-stage builds.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY projects/mock_providers/pyproject.toml ./projects/mock_providers/
# Install ONLY the mock_providers dependencies
RUN uv sync --frozen --no-dev --package mock-providers

# Stage 2: Final clean runtime image
FROM python:3.14-alpine

WORKDIR /app

# Copy the generated virtual environment
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the required application source code
# `app` is needed because mock_providers imports `app.domain.enums`
COPY projects/liquidity_orchestrator/app ./app
COPY projects/mock_providers ./mock_providers

CMD ["python", "-m", "mock_providers.main"]
