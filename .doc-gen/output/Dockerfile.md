# Dockerfile

**Path:** Dockerfile
**Syntax:** text
**Generated:** 2026-05-13 22:16:06

```
# =============================================================================
# Dockerfile for designing-gemma
# Local LLM experiment framework runner
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
COPY experiments/ experiments/

# Install package and dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Entry point is the CLI command
ENTRYPOINT ["designing-gemma"]

```
