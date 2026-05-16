# designing-gemma-context-logging.md

**Path:** docs/change/designing-gemma-context-logging.md
**Syntax:** markdown
**Generated:** 2026-05-15 14:53:19

```markdown
# Changeset: experiment_runner.py — context logging
## File: `src/designing_gemma/experiment_runner.py`

---

### Overview

After `repo_context` is built and assigned to `base_context`, write a
`results/context_latest.txt` snapshot showing exactly what Gemma receives.
File is overwritten on every run. Header lines make it self-explanatory
when opened for debugging.

---

### Change 1 — Add `_write_context_snapshot()` helper

**Location:** Insert after `_write_output()`, before the
`# === Single experiment run ===` section.

**BEFORE:**
```python
def _write_output(results_dir: Path, filename: str, text: str) -> Path:
    """Write generated output to results dir. Returns the output path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / filename
    out_path.write_text(text, encoding="utf-8")
    return out_path


# =============================================================================
# Single experiment run
# =============================================================================
```

**AFTER:**
```python
def _write_output(results_dir: Path, filename: str, text: str) -> Path:
    """Write generated output to results dir. Returns the output path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / filename
    out_path.write_text(text, encoding="utf-8")
    return out_path


def _write_context_snapshot(
    results_dir: Path,
    context_text: str,
    repo_key: str,
    manifest_path: str,
    truncated: bool,
) -> None:
    """
    Write context_latest.txt to results_dir for debugging.

    Records exactly what was injected as {{ repo_context }} for this run.
    Overwritten on every run — always reflects the most recent build.

    Args:
        results_dir:   Experiment results directory.
        context_text:  The formatted repo context string.
        repo_key:      Repo identifier from config (e.g. "dev_utils").
        manifest_path: Manifest path used for skeleton build.
        truncated:     Whether the context was truncated at the char limit.
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "context_latest.txt"
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    char_count = len(context_text)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# context_latest.txt — repo context snapshot\n")
        f.write(f"# Generated : {timestamp}\n")
        f.write(f"# Repo      : {repo_key}\n")
        f.write(f"# Manifest  : {manifest_path}\n")
        f.write(f"# Chars     : {char_count:,}\n")
        f.write(f"# Truncated : {truncated}\n")
        f.write("#\n")
        f.write(context_text)


# =============================================================================
# Single experiment run
# =============================================================================
```

---

### Change 2 — Call `_write_context_snapshot()` after repo context is built

**BEFORE:**
```python
            result = read_repo_context(skeleton_data, max_chars)
            base_context["repo_context"] = result["context_text"]
            if result["truncated"]:
                print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
```

**AFTER:**
```python
            result = read_repo_context(skeleton_data, max_chars)
            base_context["repo_context"] = result["context_text"]
            _write_context_snapshot(
                results_dir,
                result["context_text"],
                repo_key,
                manifest_path,
                result["truncated"],
            )
            if result["truncated"]:
                print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
```

**Why:** `_write_context_snapshot()` is called immediately after the
context is assigned, so the file always reflects what was actually
injected into the prompt — including whether truncation occurred.
Placed before the truncation warning print so the file exists on disk
by the time any warning is shown.

```
