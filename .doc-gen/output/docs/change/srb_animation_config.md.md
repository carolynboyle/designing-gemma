# srb_animation_config.md

**Path:** docs/change/srb_animation_config.md
**Syntax:** markdown
**Generated:** 2026-05-14 07:38:25

```markdown
# Changeset: skeleton_reader.py and repo_reader.py
## designing-gemma

Adds two new modules that give Gemma accurate structural context about target
repos without injecting raw source files. Gemma receives a compact skeleton
(imports, classes, function signatures) rather than full file contents.

---

## 1. New file: src/designing_gemma/skeleton_reader.py

**File path:** `src/designing_gemma/skeleton_reader.py`

**BEFORE:** File does not exist.

**AFTER:** See attached `skeleton_reader.py`.

**What it does:**
- Reads `.doc-gen/manifest.yml` from a target repo
- Extracts structural summaries from Python files using `ast.parse()`
  — imports, class names, function signatures
- Includes non-Python files as-is if under `DEFAULT_SIZE_LIMIT` (5000 chars)
- Skips hardcoded patterns: `.egg-info`, `__pycache__`, `.pytest_cache`,
  `.git`, `.doc-gen`
- Writes output to `.doc-gen/manifest.skel`
- Exposes a CLI entry point: `designing-gemma-skel <repo_path>`

---

## 2. New file: src/designing_gemma/repo_reader.py

**File path:** `src/designing_gemma/repo_reader.py`

**BEFORE:** File does not exist.

**AFTER:** See attached `repo_reader.py`.

**What it does:**
- Reads `.doc-gen/manifest.skel`
- Formats each entry as a readable text block with path header
- Enforces a character budget (`DEFAULT_MAX_CHARS` = 40,000)
- Truncates at file boundaries — never mid-file
- Returns a dict with `context_text` ready for `{{ repo_context }}` injection
- Raises `RepoReaderError` with a helpful message if `manifest.skel` is missing

---

## 3. pyproject.toml

**File path:** `pyproject.toml`

**BEFORE:**
```toml
[project.scripts]
designing-gemma = "designing_gemma.experiment_runner:main"
```

**AFTER:**
```toml
[project.scripts]
designing-gemma      = "designing_gemma.experiment_runner:main"
designing-gemma-skel = "designing_gemma.skeleton_reader:main"
```

**Why:** Registers `designing-gemma-skel` as a CLI command inside the container.
Run once per repo before experiments that require repo context:
```bash
designing-gemma-skel /repos/dev-utils
designing-gemma-skel /repos/sr-barbara
```

---

## After Applying

1. Rebuild the container: `podman-compose build`
2. Run skeleton against both repos:
   ```bash
   podman-compose run --rm runner designing-gemma-skel /repos/dev-utils
   podman-compose run --rm runner designing-gemma-skel /repos/sr-barbara
   ```
   This writes `.doc-gen/manifest.skel` into each repo.
3. Run `pytest` — new tests for both modules to be written separately.
4. Update experiment configs to add `repo_read` blocks (separate changeset).

---

## Notes for filekit / skeletonkit

- `_extract_python_skeleton()` in `skeleton_reader.py` is the core reusable
  function — pure input/output, no side effects, easy to extract later.
- The `ast` approach is Python-specific. A future filekit would need language
  detection and per-language strategies for shell scripts, YAML, etc.
- The doc-gen `manifest.yml` dependency is a pragmatic coupling. A standalone
  skeletonkit tool should accept a repo path directly and not require doc-gen.
- egg-info exclusion is handled by `HARDCODED_SKIP_PATTERNS` here. The same
  pattern string should be added to doc-gen's `ignore-patterns.txt` so
  egg-info files stop appearing in `manifest.yml` in the first place.

```
