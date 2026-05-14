# docker-compose.yml

**Path:** docker-compose.yml
**Syntax:** yaml
**Generated:** 2026-05-14 07:38:25

```yaml
# =============================================================================
# docker-compose.yml for designing-gemma
# Runs the experiment framework against Ollama on the host
# =============================================================================
#
# Usage:
#   docker compose build
#   docker compose run --rm runner
#
# The runner will prompt you interactively for which experiments to run.
# Repos (sr-barbara, dev-utils) are mounted as volumes so Gemma can read/modify them.
#
# =============================================================================

services:
  runner:
    build: .
    container_name: designing-gemma-runner
    
    # Mount the project and target repos
    volumes:
      - .:/app
      - ../sr-barbara:/repos/sr-barbara
      - ../dev-utils:/repos/dev-utils
    
    # Point to Ollama on the host
    environment:
      OLLAMA_HOST: ${OLLAMA_HOST:-localhost}
      OLLAMA_PORT: ${OLLAMA_PORT:-11434}
    
    # Keep container alive for interactive prompts
    stdin_open: true
    tty: true
    
    # Don't remove on exit — keep results for inspection
    restart: "no"

```
