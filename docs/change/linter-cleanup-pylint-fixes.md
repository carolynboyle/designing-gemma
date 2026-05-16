# Changeset: Pylint Fixes — experiment_runner.py
## designing-gemma

Fixes all pylint errors and warnings introduced by the per-file iteration
changeset. Two real errors (used-before-assignment), plus style fixes
(line length, import placement, subprocess check, module docstring,
disable comments for intentional argument counts).

---

## 1. Add module docstring and move `subprocess` import to top

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE** (lines 1–22):
```python
# =============================================================================
# designing_gemma/experiment_runner.py
# Orchestrates experiment runs end-to-end.
# Interactive CLI — pauses between experiments for human review.
# Entry point: designing-gemma (see pyproject.toml)
# =============================================================================

import io
import re
import sys
import datetime
from pathlib import Path

import yaml
```

**AFTER:**
```python
# =============================================================================
# designing_gemma/experiment_runner.py
# Orchestrates experiment runs end-to-end.
# Interactive CLI — pauses between experiments for human review.
# Entry point: designing-gemma (see pyproject.toml)
# =============================================================================
"""
Experiment runner for the designing-gemma LLM evaluation framework.

Orchestrates experiment runs end-to-end: loads config, builds repo context,
iterates over packages or files, renders prompts, calls Ollama, and writes
results. Interactive CLI — pauses between experiments for human review.
"""

import io
import re
import sys
import datetime
import subprocess
from pathlib import Path

import yaml
```

**Why:** Module docstring satisfies C0114. Moving `subprocess` to the top
satisfies C0415 (import-outside-toplevel). It is a stdlib module with no
side effects — safe to import unconditionally.

---

## 2. Fix `_run_pylint()` — remove local import, add `check=False`

**BEFORE:**
```python
def _run_pylint(abs_path: Path) -> str:
    """
    Run pylint against a single file and return the JSON report as a string.

    Pylint exits non-zero on any finding — we capture output regardless of
    exit code and treat the JSON as the result. If pylint is not available
    or the run fails entirely, returns a descriptive error string instead.

    Args:
        abs_path: Absolute path to the Python file to lint.

    Returns:
        JSON string from pylint stdout, or an error message string.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", str(abs_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
```

**AFTER:**
```python
def _run_pylint(abs_path: Path) -> str:
    """
    Run pylint against a single file and return the JSON report as a string.

    Pylint exits non-zero on any finding — we capture output regardless of
    exit code and treat the JSON as the result. If pylint is not available
    or the run fails entirely, returns a descriptive error string instead.

    Args:
        abs_path: Absolute path to the Python file to lint.

    Returns:
        JSON string from pylint stdout, or an error message string.
    """
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", str(abs_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
```

**Why:** Removes the local import (now at top of file). Adds `check=False`
to satisfy W1510 — explicitly documents that non-zero exit is expected and
handled by the returncode check below.

---

## 3. Fix `_output_filename()` — disable too-many-arguments

**BEFORE:**
```python
def _output_filename(
    run_id: str,
    model: str,
    prompt_label: str,
    corpus_label: str | None = None,
    package_name: str | None = None,
    file_label: str | None = None,
) -> str:
    """Build a result filename from run metadata."""
```

**AFTER:**
```python
def _output_filename(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    run_id: str,
    model: str,
    prompt_label: str,
    corpus_label: str | None = None,
    package_name: str | None = None,
    file_label: str | None = None,
) -> str:
    """Build a result filename from run metadata."""
```

**Why:** Six arguments is correct design here — each is a distinct piece of
run metadata needed to construct a unique filename. Refactoring to a dataclass
would add complexity without benefit. Disable comment makes the intent explicit.

---

## 4. Fix `_write_context_snapshot()` — disable too-many-arguments

**BEFORE:**
```python
def _write_context_snapshot(
    results_dir: Path,
    context_text: str,
    repo_key: str,
    manifest_path: str,
    truncated: bool,
    package_name: str | None = None,
) -> None:
    """
    Write context_latest.txt to results_dir for debugging.
```

**AFTER:**
```python
def _write_context_snapshot(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    results_dir: Path,
    context_text: str,
    repo_key: str,
    manifest_path: str,
    truncated: bool,
    package_name: str | None = None,
) -> None:
    """
    Write context_latest.txt to results_dir for debugging.
```

**Why:** Same reasoning as `_output_filename` — these are distinct,
required pieces of snapshot metadata. Pre-existing issue now visible
because pylint is running against the file.

---

## 5. Fix E0601 — initialize `repo_root_path` before the if/elif block

**BEFORE** (line 472):
```python
# Determine iteration mode — per-package, per-file, or single pass
    packages = []
    py_files  = []

    if skeleton_data and repo_read.get("per_package", False):
```

**AFTER:**
```python
    # Determine iteration mode — per-package, per-file, or single pass
    packages       = []
    py_files       = []
    repo_root_path = Path()

    if skeleton_data and repo_read.get("per_package", False):
```

**Why:** `repo_root_path` is assigned inside the `elif` branch but
consumed later in the `if py_files:` block, which is outside the `elif`.
Pylint correctly flags this as used-before-assignment. Initializing to
`Path()` (empty path) is safe — the per-file block only runs when
`py_files` is non-empty, which only happens when the `elif` branch ran
and assigned `repo_root_path` correctly. Also fixes the indentation error
on line 472 (was 0-indented, should be 4-space indented inside the function).

---

## 6. Fix E0606 — initialize `max_chars` before the `if repo_read:` block

**BEFORE** (line 444):
```python
    # Load repo context if experiment specifies repo_read
    repo_read     = config.get("repo_read")
    skeleton_data = None

    if repo_read:
        repo_key       = repo_read.get("repo")
        repo_root      = Path(repos.get(repo_key, ""))
        max_chars      = repo_read.get("max_chars", 40_000)
```

**AFTER:**
```python
    # Load repo context if experiment specifies repo_read
    repo_read     = config.get("repo_read")
    skeleton_data = None
    max_chars     = 40_000

    if repo_read:
        repo_key       = repo_read.get("repo")
        repo_root      = Path(repos.get(repo_key, ""))
        max_chars      = repo_read.get("max_chars", max_chars)
```

**Why:** `max_chars` is used at line 644 inside the packages loop, which
is reachable even when `repo_read` is None (the packages list falls
through to `[None]`). Pylint correctly identifies the conditional
assignment as a possible unassigned use. Initializing to the default
value before the block and using it as the fallback inside the block
makes the intent explicit and removes the ambiguity.

---

## 7. Fix C0301 — wrap long lines

All six offending lines. Changes are line-wrapping only — no logic change.

**Line 489:**
```python
# BEFORE
            print("  WARNING: no packages found in skeleton data — running without per-package iteration.")

# AFTER
            print(
                "  WARNING: no packages found in skeleton data"
                " — running without per-package iteration."
            )
```

**Line 507:**
```python
# BEFORE
            print("  WARNING: no Python files found in skeleton data — running without per-file iteration.")

# AFTER
            print(
                "  WARNING: no Python files found in skeleton data"
                " — running without per-file iteration."
            )
```

**Line 589:**
```python
# BEFORE
                        "experiment_version": config.get("experiment", {}).get("experiment_version", 1),

# AFTER
                        "experiment_version": (
                            config.get("experiment", {}).get("experiment_version", 1)
                        ),
```
*(This line appears in the per-file log_entry block.)*

**Line 634:**
```python
# BEFORE
            _subheader(f"Package: {package_name}  ({packages.index(package_name) + 1}/{len(packages)})")

# AFTER
            pkg_num = packages.index(package_name) + 1
            _subheader(
                f"Package: {package_name}  ({pkg_num}/{len(packages)})"
            )
```

**Line 655:**
```python
# BEFORE
                    print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")

# AFTER
                    print(
                        f"  WARNING: repo context truncated"
                        f" — {result['files_excluded']} file(s) omitted"
                    )
```

**Line 735:**
```python
# BEFORE
                        "experiment_version": config.get("experiment", {}).get("experiment_version", 1),

# AFTER
                        "experiment_version": (
                            config.get("experiment", {}).get("experiment_version", 1)
                        ),
```
*(This line appears in the per-package log_entry block.)*

---

## Expected pylint result after applying

Remaining warnings will be:
- `R0914` too-many-locals — pre-existing, `_run_experiment()` is a known
  large function. Not introduced by this changeset.
- `W0603` global-statement — pre-existing `RUN_ALL` global flag. By design.
- `R0912/R0915` too-many-branches/statements — pre-existing.
- `R1702` too-many-nested-blocks — pre-existing.

All of the above are design-level complaints about `_run_experiment()` as
a whole, not correctness issues. They are pre-existing and out of scope
for this changeset.

## Commit message

```
fix: pylint errors and warnings from per-file iteration changeset
```
