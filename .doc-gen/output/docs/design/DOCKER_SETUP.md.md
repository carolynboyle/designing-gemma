# DOCKER_SETUP.md

**Path:** docs/design/DOCKER_SETUP.md
**Syntax:** markdown
**Generated:** 2026-05-14 07:38:25

```markdown
# Designing Gemma — Local Test & Mac Deployment Guide

## Part 1: Local Testing (MX Linux)

Test the Docker build locally before copying to the Mac.

### Prerequisites

- Docker installed and running
- designing-gemma repo cloned to `~/projects/designing-gemma`
- sr-barbara repo cloned to `~/projects/sr-barbara`
- dev-utils repo cloned to `~/projects/dev-utils`

### Steps

1. **Navigate to the project:**
   ```bash
   cd ~/projects/designing-gemma
   ```

2. **Build the Docker image:**
   ```bash
   docker compose build
   ```
   
   Watch for errors. If the build completes without errors, proceed to step 3. If there are errors, fix them before continuing.

3. **Verify the build succeeded:**
   ```bash
   docker images | grep designing-gemma
   ```
   
   You should see an image listed. The build is successful.

4. **Test that the image can start** (won't connect to Ollama, but verifies the container runs):
   ```bash
   docker compose run --rm runner --help
   ```
   
   This should print the help output from the `designing-gemma` CLI without errors.

### Success Criteria

- ✅ `docker compose build` completes without errors
- ✅ Image appears in `docker images`
- ✅ Container starts and runs the CLI without crashing

If all three pass, the build is solid. Proceed to Part 2.

---

## Part 2: Mac Deployment

Once local testing passes, set up on the Mac.

### Prerequisites on Mac

- Docker CLI installed and running
- Ollama installed and running natively on the Mac
- Three repos cloned to `~/projects/`:
  - `sr-barbara`
  - `dev-utils`
  - `designing-gemma`

### Step 1: Verify Ollama is Running

```bash
curl http://localhost:11434
```

You should get a response (even if it's just HTML). If you get "connection refused", start Ollama:

```bash
ollama serve
```

(This runs in the foreground. Open a new terminal for the next steps.)

### Step 2: Navigate to the Project

```bash
cd ~/projects/designing-gemma
```

### Step 3: Verify Files Are in Place

Check that these files exist in the designing-gemma root:

```bash
ls -la Dockerfile docker-compose.yml
```

Both should be present. If not, copy them from your local test environment.

### Step 4: Verify Updated ollama_client.py

Check that `src/designing_gemma/ollama_client.py` imports `os` and reads the OLLAMA_HOST env var:

```bash
head -20 src/designing_gemma/ollama_client.py | grep "import os"
```

Should see `import os`. If not, update the file:

```python
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"
```

### Step 5: Build the Image

```bash
docker compose build
```

This will take a minute or two. Wait for it to complete without errors.

### Step 6: Test the Runner

Start the interactive runner:

```bash
docker compose run --rm runner
```

You should see:

```
Designing Gemma  v0.1.0
  A structured experiment framework for local LLM evaluation.
  Don't Panic.

Checking Ollama connection...
  Ollama is running.

  8 experiment(s) enabled:
  
    01  readme_gen                   risk: NONE
    02  linter_cleanup               risk: LOW
    03  srb_animation                risk: MEDIUM
    04  pkg_restructure              risk: HIGH
    05  capstone_summary             risk: NONE (disabled)
    06  srb_sentence_gen             risk: NONE
    07  capstone_summary             risk: NONE
    08  capstone_readme              risk: NONE

Press ENTER to begin, 'q' to quit:
```

Press `q` to quit. The runner is working.

### Step 7: Commit and Push

Once everything works:

```bash
cd ~/projects/designing-gemma
git add Dockerfile docker-compose.yml src/designing_gemma/ollama_client.py
git commit -m "Add Docker containerization for experiment runner"
git push
```

---

## Troubleshooting

**"docker: command not found"**
- Docker CLI is not installed or not in PATH. Install Docker Desktop or Docker CLI via Homebrew.

**"Ollama is running" but connection refused**
- Ollama is not actually running. Start it: `ollama serve`

**Build fails with permission errors**
- Make sure you're not running `docker compose` with `sudo`. Docker should be configured to run without sudo.

**Container starts but immediately exits**
- Check that `experiments/` folders have prompts (`.md` files). Empty prompts will cause failures during run.

---

## Notes

- The runner is interactive. It will pause between experiments and ask for confirmation.
- Results are written to `experiments/*/results/` inside the container and mounted back to the host.
- Ollama must stay running in a separate terminal while the container runs.
- If you modify prompts or config files, rebuild the image: `docker compose build`

```
