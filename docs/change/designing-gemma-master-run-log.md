# Changeset: Master Run Log in data/
## designing-gemma

Adds `data/run_log_master.yaml` as the single cross-experiment run log.
Every `_append_run_log()` call writes to both the experiment's own
`results/run_log.yaml` and the master log. Experiment 06 (capstone_summary)
reads from the master log via `inject_run_log: true`.

Previously `inject_run_log` read from the experiment's own results dir,
which is always empty for experiment 06 since it doesn't generate runs
of its own. The master log collects entries from all experiments.

---

## 1. experiment_runner.py — add master log path constant

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE** (near top, after SESSION_LOG_PATH):
```python
# Session log path — project root, overwritten every run.
# Rename to keep: e.g. session_log_2026-05-14.txt
SESSION_LOG_PATH = "session_log.txt"
```

**AFTER:**
```python
# Session log path — project root, overwritten every run.
# Rename to keep: e.g. session_log_2026-05-14.txt
SESSION_LOG_PATH = "session_log.txt"

# Master run log — accumulates entries from all experiments.
# Read by experiment 06 (capstone_summary) via inject_run_log: true.
MASTER_RUN_LOG_PATH = "data/run_log_master.yaml"
```

**Why:** Single named constant — easy to find, easy to change.

---

## 2. experiment_runner.py — update _append_run_log() to also write master log

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE:**
```python
def _append_run_log(results_dir: Path, entry: dict) -> None:
    """Append a single run entry to results/run_log.yaml."""
    log_path = results_dir / "run_log.yaml"
    log = []
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            log = yaml.safe_load(f) or []
    log.append(entry)
    with log_path.open("w", encoding="utf-8") as f:
        yaml.dump(log, f, allow_unicode=True, sort_keys=False)
```

**AFTER:**
```python
def _append_run_log(results_dir: Path, entry: dict) -> None:
    """
    Append a single run entry to results/run_log.yaml and
    data/run_log_master.yaml.

    The per-experiment log is scoped to that experiment's results dir.
    The master log accumulates entries from all experiments and is read
    by experiment 06 (capstone_summary) via inject_run_log: true.
    """
    # Per-experiment log
    log_path = results_dir / "run_log.yaml"
    log = []
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            log = yaml.safe_load(f) or []
    log.append(entry)
    with log_path.open("w", encoding="utf-8") as f:
        yaml.dump(log, f, allow_unicode=True, sort_keys=False)

    # Master log
    master_path = Path(MASTER_RUN_LOG_PATH)
    master_path.parent.mkdir(parents=True, exist_ok=True)
    master_log = []
    if master_path.exists():
        with master_path.open("r", encoding="utf-8") as f:
            master_log = yaml.safe_load(f) or []
    master_log.append(entry)
    with master_path.open("w", encoding="utf-8") as f:
        yaml.dump(master_log, f, allow_unicode=True, sort_keys=False)
```

**Why:** Every run now writes to both logs simultaneously. The master
log is always current without any extra steps.

---

## 3. experiment_runner.py — update inject_run_log to read master log

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE:**
```python
    # Inject run_log if experiment requests it
    if config.get("inject_run_log", False):
        run_log_text = _load_run_log(results_dir)
        if run_log_text:
            base_context["run_log"] = run_log_text
            print(f"  Run log injected ({len(run_log_text):,} chars)")
        else:
            print("  WARNING: inject_run_log requested but no run_log.yaml found")
```

**AFTER:**
```python
    # Inject run_log if experiment requests it
    if config.get("inject_run_log", False):
        master_path = Path(MASTER_RUN_LOG_PATH)
        run_log_text = _load_run_log(master_path.parent) if master_path.exists() else ""
        if run_log_text:
            base_context["run_log"] = run_log_text
            print(f"  Run log injected ({len(run_log_text):,} chars)")
        else:
            print("  WARNING: inject_run_log requested but data/run_log_master.yaml not found")
            print("           Run experiments 01-05 first to populate the master log.")
```

**Why:** Reads from the master log rather than the experiment's own
results dir. The improved warning message tells you exactly what to
do if the file is missing.

---

## 4. _load_run_log() — update to accept a Path directly

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE:**
```python
def _load_run_log(results_dir: Path) -> str:
    """
    Load run_log.yaml and return as a YAML-formatted string.

    Used to inject {{ run_log }} into capstone summary prompts.
    Returns an empty string if no run log exists yet.

    Args:
        results_dir: Experiment results directory.

    Returns:
        YAML string of run log contents, or empty string if not found.
    """
    log_path = results_dir / "run_log.yaml"
    if not log_path.exists():
        return ""
    with log_path.open("r", encoding="utf-8") as f:
        log = yaml.safe_load(f) or []
    return yaml.dump(log, allow_unicode=True, sort_keys=False)
```

**AFTER:**
```python
def _load_run_log(log_dir: Path, filename: str = "run_log.yaml") -> str:
    """
    Load a run log file and return as a YAML-formatted string.

    Used to inject {{ run_log }} into capstone summary prompts.
    Returns an empty string if no log file exists yet.

    Args:
        log_dir:  Directory containing the log file.
        filename: Log filename (default: run_log.yaml).

    Returns:
        YAML string of run log contents, or empty string if not found.
    """
    log_path = log_dir / filename
    if not log_path.exists():
        return ""
    with log_path.open("r", encoding="utf-8") as f:
        log = yaml.safe_load(f) or []
    return yaml.dump(log, allow_unicode=True, sort_keys=False)
```

**Why:** Accepts a directory + optional filename rather than assuming
`run_log.yaml`. Allows the master log call to pass `data/` as the
directory with `run_log_master.yaml` as the filename. Backward compatible
— existing per-experiment calls still work with the default filename.

---

## 5. Update inject_run_log to use new _load_run_log signature

Update the call added in change 3 to use the filename parameter:

```python
    # Inject run_log if experiment requests it
    if config.get("inject_run_log", False):
        master_path = Path(MASTER_RUN_LOG_PATH)
        run_log_text = (
            _load_run_log(master_path.parent, master_path.name)
            if master_path.exists()
            else ""
        )
        if run_log_text:
            base_context["run_log"] = run_log_text
            print(f"  Run log injected ({len(run_log_text):,} chars)")
        else:
            print("  WARNING: inject_run_log requested but data/run_log_master.yaml not found")
            print("           Run experiments 01-05 first to populate the master log.")
```

---

## After applying

1. Apply all changes to `experiment_runner.py`
2. Rebuild container: `podman-compose build`
3. Run experiments 01-05 — each run now populates `data/run_log_master.yaml`
4. Run experiment 06 — `{{ run_log }}` will render with all prior results

## Commit message

```
feat: add master run log in data/ — fixes experiment 06 inject_run_log
```
