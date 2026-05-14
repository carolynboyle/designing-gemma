# designing-gemma-env-fix.md

**Path:** docs/change/designing-gemma-env-fix.md
**Syntax:** markdown
**Generated:** 2026-05-13 22:16:06

```markdown
# Changeset: Ollama Environment Variable Fix
## designing-gemma

Removes hardcoded OS-specific Ollama connection values from source files.
Implements split `OLLAMA_HOST` / `OLLAMA_PORT` variables per `config_rules.md`.

---

## 1. docker-compose.yml

**File path:** `docker-compose.yml`

**BEFORE:**
```yaml
environment:
  OLLAMA_HOST: http://host.containers.internal:11434
```

**AFTER:**
```yaml
environment:
  OLLAMA_HOST: ${OLLAMA_HOST:-localhost}
  OLLAMA_PORT: ${OLLAMA_PORT:-11434}
```

**Why:** The hardcoded value was OS- and runtime-specific (Podman on macOS).
It silently broke on any other platform. Variables now come from `.env` with
safe fallbacks for local development without a `.env` file.

---

## 2. src/designing_gemma/ollama_client.py

**File path:** `src/designing_gemma/ollama_client.py`

**BEFORE:**
```python
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"
```

**AFTER:**
```python
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"
```

**Why:** Splits the single `OLLAMA_HOST` variable (which previously held a full
URL) into separate host and port variables, matching the compose file and
`.env` templates. The URL is constructed at runtime from the two parts.
Fallbacks preserve local development behaviour when no `.env` is present.

---

## 3. New file: .env.example

**File path:** `.env.example`

**BEFORE:** File does not exist.

**AFTER:**
```dotenv
# =============================================================================
# .env.example
# Copy the appropriate OS template to .env and fill in values:
#   macOS:   cp .env.mac.example .env
#   Linux:   cp .env.linux.example .env
#   Windows: copy .env.windows.example .env
#
# .env is gitignored and must never be committed.
# =============================================================================

# --- Ollama / Model Inference ---
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
```

---

## 4. New file: .env.mac.example

**File path:** `.env.mac.example`

**BEFORE:** File does not exist.

**AFTER:**
```dotenv
# =============================================================================
# .env.mac.example — macOS
# Copy to .env and adjust for your setup.
#
# The OLLAMA_HOST value below is correct for Docker Desktop on macOS.
# If you are using Podman, use: host.containers.internal
# =============================================================================

# --- Ollama / Model Inference ---
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
```

---

## 5. New file: .env.linux.example

**File path:** `.env.linux.example`

**BEFORE:** File does not exist.

**AFTER:**
```dotenv
# =============================================================================
# .env.linux.example — Linux
# Copy to .env and adjust for your setup.
# =============================================================================

# --- Ollama / Model Inference ---
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
```

---

## 6. .gitignore addition

**File path:** `.gitignore`

**BEFORE:**
```
# (existing entries)
```

**AFTER:** Add the following if not already present:
```gitignore
# Environment — never commit
.env
*.local.env
```

**Why:** The `.env.example`, `.env.mac.example`, and `.env.linux.example` files
are committed as templates. The actual `.env` file must never be committed.

---

## After Applying

1. Copy the appropriate template: `cp .env.mac.example .env`
2. Rebuild the container: `podman-compose build`
3. Run: `podman-compose run --rm runner`
4. Verify Ollama is reachable — the runner prints a connection check on startup.

```
