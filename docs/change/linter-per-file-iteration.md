# Changeset: Per-File Iteration for Linter Cleanup Experiment
## designing-gemma

Adds per-file iteration mode to `experiment_runner.py`, mirroring the
existing per-package pattern. Adds `repo_read` and `per_file: true` to
the linter cleanup config so target files are discovered from the skeleton
rather than hardcoded anywhere. Adds pylint as a dev dependency.

---

## 1. src/designing_gemma/experiment_runner.py
### 1a. Add `_discover_python_files()`

**File path:** `src/designing_gemma/experiment_runner.py`

Add after `_filter_skeleton_for_package()` (around line 307):

**BEFORE:**
```python
# =============================================================================
# Single experiment run
# =============================================================================
```

**AFTER:**
```python
def _discover_python_files(skeleton_data: dict) -> list[str]:
    """
    Discover Python source files from skeleton data.

    Returns a sorted list of file paths (relative to repo root) for all
    entries with type 'python' or 'python_unparseable'. Used by the
    per-file iteration mode in linter_cleanup and similar experiments.

    Args:
        skeleton_data: Output of build_skeleton().

    Returns:
        Sorted list of relative file path strings, e.g.
        ["python/dbkit/dbkit.py", "python/fletcher/fletcher.py"]
    """
    files = []
    for entry in skeleton_data.get("files", []):
        if entry.get("type") in ("python", "python_unparseable"):
            path = entry.get("path", "")
            if path:
                files.append(path)
    return sorted(files)


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
        # pylint exits 0 (clean), 4 (warnings), 8 (errors), 16 (usage error)
        # anything except 16 (usage/crash) is a valid report
        if result.returncode == 16 or (not result.stdout and result.returncode != 0):
            return f"[pylint error: {result.stderr.strip() or 'no output'}]"
        return result.stdout or "[]"
    except FileNotFoundError:
        return "[pylint not found — is it installed in this environment?]"


# =============================================================================
# Single experiment run
# =============================================================================
```

**Why:** Parallel to `_discover_packages()` and the pylint subprocess wrapper.
Pylint is intentionally run live (not pre-generated) so the report always
reflects the current state of the file. Exit code 16 is the only true failure
mode — all other codes mean pylint ran and produced output.

---

### 1b. Add `file_label` parameter to `_output_filename()`

**BEFORE:**
```python
def _output_filename(
    run_id: str,
    model: str,
    prompt_label: str,
    corpus_label: str | None = None,
    package_name: str | None = None,
) -> str:
    """Build a result filename from run metadata."""
    model_slug = model.replace(":", "-").replace("/", "-")
    parts = [run_id, model_slug, prompt_label]
    if package_name:
        parts.append(package_name)
    if corpus_label:
        parts.append(corpus_label)
    return "_".join(parts) + ".txt"
```

**AFTER:**
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
    model_slug = model.replace(":", "-").replace("/", "-")
    parts = [run_id, model_slug, prompt_label]
    if package_name:
        parts.append(package_name)
    if file_label:
        parts.append(file_label)
    if corpus_label:
        parts.append(corpus_label)
    return "_".join(parts) + ".txt"
```

**Why:** Per-file output files need the source filename in their name so
results are identifiable. `file_label` is derived from the filename stem
(e.g. `dbkit` from `python/dbkit/dbkit.py`).

---

### 1c. Add per-file iteration branch in `_run_experiment()`

This goes in `_run_experiment()`, immediately after the per-package block.
The per-package block ends at the `if not packages:` guard — add the
per-file block right after it, before the `for package_name in packages:`
loop begins.

**BEFORE:**
```python
    # Determine iteration mode — per-package or single pass
    packages = []
    if skeleton_data and repo_read.get("per_package", False):
        packages = _discover_packages(skeleton_data)
        if packages:
            print(f"\n  Packages found: {packages}")
            pkg_choice = _pause(
                "\nPress ENTER to confirm between packages, 'a' to run all, 'q' to quit: "
            )
            if pkg_choice == "q":
                print("Quitting.")
                sys.exit(0)
            if pkg_choice == "a":
                RUN_ALL = True
        else:
            print("  WARNING: no packages found in skeleton data — running without per-package iteration.")

    # If no packages discovered (or per_package not set), run as single pass
    if not packages:
        packages = [None]

    for package_name in packages:
```

**AFTER:**
```python
    # Determine iteration mode — per-package, per-file, or single pass
    packages = []
    py_files  = []

    if skeleton_data and repo_read.get("per_package", False):
        packages = _discover_packages(skeleton_data)
        if packages:
            print(f"\n  Packages found: {packages}")
            pkg_choice = _pause(
                "\nPress ENTER to confirm between packages, 'a' to run all, 'q' to quit: "
            )
            if pkg_choice == "q":
                print("Quitting.")
                sys.exit(0)
            if pkg_choice == "a":
                RUN_ALL = True
        else:
            print("  WARNING: no packages found in skeleton data — running without per-package iteration.")

    elif skeleton_data and repo_read.get("per_file", False):
        repo_root_path = Path(repos.get(repo_read.get("repo", ""), ""))
        py_files = _discover_python_files(skeleton_data)
        if py_files:
            print(f"\n  Python files found: {len(py_files)}")
            for f in py_files:
                print(f"    {f}")
            file_choice = _pause(
                "\nPress ENTER to confirm between files, 'a' to run all, 'q' to quit: "
            )
            if file_choice == "q":
                print("Quitting.")
                sys.exit(0)
            if file_choice == "a":
                RUN_ALL = True
        else:
            print("  WARNING: no Python files found in skeleton data — running without per-file iteration.")

    # If no packages or files discovered (or neither mode set), run as single pass
    if not packages:
        packages = [None]

    for package_name in packages:
```

**Why:** Adds a parallel `elif` branch for per-file mode. Uses `elif` so
the modes are mutually exclusive — a config can't accidentally set both.
`repo_root_path` is resolved here once for use in the file loop below.

---

### 1d. Add per-file loop after the existing packages loop

The existing packages loop ends at `return True`. Add the per-file loop
**inside** the packages loop, after the per-package context-building block
but the file loop replaces nothing — it is a separate iteration axis.

Actually, the cleanest approach: the per-file loop runs **instead of** the
packages loop when `py_files` is populated. Replace the final section of
`_run_experiment()` as follows.

**BEFORE** (from the `for package_name in packages:` loop to `return True`):
```python
    for package_name in packages:
        if package_name:
            _subheader(f"Package: {package_name}  ({packages.index(package_name) + 1}/{len(packages)})")

        # Build repo context for this package (or full repo if no package)
        if skeleton_data:
            try:
                if package_name:
                    pkg_skeleton = _filter_skeleton_for_package(skeleton_data, package_name)
                else:
                    pkg_skeleton = skeleton_data

                result = read_repo_context(pkg_skeleton, max_chars)
                base_context["repo_context"] = result["context_text"]
                _write_context_snapshot(
                    results_dir,
                    result["context_text"],
                    repo_key,
                    manifest_path,
                    result["truncated"],
                    package_name=package_name,
                )
                if result["truncated"]:
                    print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
            except RepoReaderError as e:
                print(f"  ERROR loading repo context: {e}")
                continue

        for prompt_def in prompts:
            prompt_file  = prompt_def.get("file")
            prompt_label = prompt_def.get("label", prompt_file)

            for corpus in corpus_list:
                corpus_label = corpus["label"] if corpus else None

                # Build Jinja2 context — start from base, add corpus if present
                context = dict(base_context)
                if package_name:
                    context["package_name"] = package_name
                if corpus:
                    try:
                        source = corpus["source"]
                        if corpus["source_type"] == "file":
                            source = str(experiment_dir / source)
                        corpus_text = load_corpus(source, corpus["source_type"])
                        context["source_text"] = corpus_text
                    except PromptError as e:
                        print(f"  ERROR loading corpus {corpus_label}: {e}")
                        continue

                # Render prompt
                try:
                    rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
                except PromptError as e:
                    print(f"  ERROR rendering prompt {prompt_file}: {e}")
                    continue

                for model_def in models:
                    model_name   = model_def.get("name")
                    model_digest = model_def.get("digest")

                    run_id = _run_id(results_dir)

                    _subheader(
                        f"{prompt_label}"
                        + (f" / {package_name}" if package_name else "")
                        + (f" / {corpus_label}" if corpus_label else "")
                        + f" / {model_name}"
                    )

                    try:
                        result = generate(
                            model=model_name,
                            prompt=rendered_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            digest=model_digest,
                            stream_to_stdout=True,
                        )
                    except OllamaError as e:
                        print(f"\n  ERROR: {e}")
                        result = {
                            "text": "",
                            "model": model_name,
                            "model_digest": model_digest,
                            "tokens_per_second": 0.0,
                            "context_length": 0,
                            "status": "failed",
                        }

                    # Write output file
                    out_filename = _output_filename(
                        run_id, model_name, prompt_label,
                        corpus_label=corpus_label,
                        package_name=package_name,
                    )
                    out_path = _write_output(results_dir, out_filename, result["text"])

                    # Append to run log
                    log_entry = {
                        "id":                 run_id,
                        "timestamp":          datetime.datetime.now().isoformat(),
                        "experiment":         name,
                        "experiment_version": config.get("experiment", {}).get("experiment_version", 1),
                        "model":              result["model"],
                        "model_digest":       result["model_digest"],
                        "prompt_file":        str(prompt_dir / prompt_file),
                        "prompt_label":       prompt_label,
                        "package":            package_name,
                        "corpus_label":       corpus_label,
                        "output_file":        str(out_path),
                        "tokens_per_second":  result["tokens_per_second"],
                        "context_length":     result["context_length"],
                        "status":             result["status"],
                        "documented":         [],
                        "tags":               [],
                        "notes":              None,
                    }
                    _append_run_log(results_dir, log_entry)

                    print(f"\n  Written : {out_path}")
                    print(f"  Speed   : {result['tokens_per_second']} tok/s")
                    print(f"  Status  : {result['status']}")

        # Per-package confirmation pause (skipped if RUN_ALL)
        if package_name and not RUN_ALL:
            remaining = len(packages) - packages.index(package_name) - 1
            if remaining > 0:
                pkg_choice = _pause(
                    f"\n  {remaining} package(s) remaining. "
                    "Press ENTER to continue, 'a' for all, 's' to skip rest, 'q' to quit: "
                )
                if pkg_choice == "q":
                    print("Quitting.")
                    sys.exit(0)
                if pkg_choice == "s":
                    print("  Skipping remaining packages.")
                    break
                if pkg_choice == "a":
                    RUN_ALL = True

    return True
```

**AFTER:**
```python
    # ==========================================================================
    # Per-file iteration mode
    # ==========================================================================
    if py_files:
        for file_idx, rel_path in enumerate(py_files):
            abs_path  = repo_root_path / rel_path
            file_stem = Path(rel_path).stem

            _subheader(f"File: {rel_path}  ({file_idx + 1}/{len(py_files)})")

            # Read file contents
            if not abs_path.exists():
                print(f"  WARNING: file not found at {abs_path} — skipping")
                continue
            file_contents = abs_path.read_text(encoding="utf-8")

            # Run pylint
            print(f"  Running pylint against {rel_path} ...")
            pylint_report = _run_pylint(abs_path)
            print(f"  Pylint report: {len(pylint_report)} chars")

            for prompt_def in prompts:
                prompt_file  = prompt_def.get("file")
                prompt_label = prompt_def.get("label", prompt_file)

                context = dict(base_context)
                context["target_file"]    = rel_path
                context["file_contents"]  = file_contents
                context["pylint_report"]  = pylint_report

                try:
                    rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
                except PromptError as e:
                    print(f"  ERROR rendering prompt {prompt_file}: {e}")
                    continue

                for model_def in models:
                    model_name   = model_def.get("name")
                    model_digest = model_def.get("digest")

                    run_id = _run_id(results_dir)

                    _subheader(
                        f"{prompt_label} / {file_stem} / {model_name}"
                    )

                    try:
                        result = generate(
                            model=model_name,
                            prompt=rendered_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            digest=model_digest,
                            stream_to_stdout=True,
                        )
                    except OllamaError as e:
                        print(f"\n  ERROR: {e}")
                        result = {
                            "text": "",
                            "model": model_name,
                            "model_digest": model_digest,
                            "tokens_per_second": 0.0,
                            "context_length": 0,
                            "status": "failed",
                        }

                    out_filename = _output_filename(
                        run_id, model_name, prompt_label,
                        file_label=file_stem,
                    )
                    out_path = _write_output(results_dir, out_filename, result["text"])

                    log_entry = {
                        "id":                 run_id,
                        "timestamp":          datetime.datetime.now().isoformat(),
                        "experiment":         name,
                        "experiment_version": config.get("experiment", {}).get("experiment_version", 1),
                        "model":              result["model"],
                        "model_digest":       result["model_digest"],
                        "prompt_file":        str(prompt_dir / prompt_file),
                        "prompt_label":       prompt_label,
                        "target_file":        rel_path,
                        "corpus_label":       None,
                        "output_file":        str(out_path),
                        "tokens_per_second":  result["tokens_per_second"],
                        "context_length":     result["context_length"],
                        "status":             result["status"],
                        "documented":         [],
                        "tags":               [],
                        "notes":              None,
                    }
                    _append_run_log(results_dir, log_entry)

                    print(f"\n  Written : {out_path}")
                    print(f"  Speed   : {result['tokens_per_second']} tok/s")
                    print(f"  Status  : {result['status']}")

            # Per-file confirmation pause (skipped if RUN_ALL)
            if not RUN_ALL:
                remaining = len(py_files) - file_idx - 1
                if remaining > 0:
                    file_choice = _pause(
                        f"\n  {remaining} file(s) remaining. "
                        "Press ENTER to continue, 'a' for all, 's' to skip rest, 'q' to quit: "
                    )
                    if file_choice == "q":
                        print("Quitting.")
                        sys.exit(0)
                    if file_choice == "s":
                        print("  Skipping remaining files.")
                        break
                    if file_choice == "a":
                        RUN_ALL = True

        return True

    # ==========================================================================
    # Per-package iteration mode (or single pass if packages = [None])
    # ==========================================================================
    for package_name in packages:
        if package_name:
            _subheader(f"Package: {package_name}  ({packages.index(package_name) + 1}/{len(packages)})")

        # Build repo context for this package (or full repo if no package)
        if skeleton_data:
            try:
                if package_name:
                    pkg_skeleton = _filter_skeleton_for_package(skeleton_data, package_name)
                else:
                    pkg_skeleton = skeleton_data

                result = read_repo_context(pkg_skeleton, max_chars)
                base_context["repo_context"] = result["context_text"]
                _write_context_snapshot(
                    results_dir,
                    result["context_text"],
                    repo_key,
                    manifest_path,
                    result["truncated"],
                    package_name=package_name,
                )
                if result["truncated"]:
                    print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
            except RepoReaderError as e:
                print(f"  ERROR loading repo context: {e}")
                continue

        for prompt_def in prompts:
            prompt_file  = prompt_def.get("file")
            prompt_label = prompt_def.get("label", prompt_file)

            for corpus in corpus_list:
                corpus_label = corpus["label"] if corpus else None

                # Build Jinja2 context — start from base, add corpus if present
                context = dict(base_context)
                if package_name:
                    context["package_name"] = package_name
                if corpus:
                    try:
                        source = corpus["source"]
                        if corpus["source_type"] == "file":
                            source = str(experiment_dir / source)
                        corpus_text = load_corpus(source, corpus["source_type"])
                        context["source_text"] = corpus_text
                    except PromptError as e:
                        print(f"  ERROR loading corpus {corpus_label}: {e}")
                        continue

                # Render prompt
                try:
                    rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
                except PromptError as e:
                    print(f"  ERROR rendering prompt {prompt_file}: {e}")
                    continue

                for model_def in models:
                    model_name   = model_def.get("name")
                    model_digest = model_def.get("digest")

                    run_id = _run_id(results_dir)

                    _subheader(
                        f"{prompt_label}"
                        + (f" / {package_name}" if package_name else "")
                        + (f" / {corpus_label}" if corpus_label else "")
                        + f" / {model_name}"
                    )

                    try:
                        result = generate(
                            model=model_name,
                            prompt=rendered_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            digest=model_digest,
                            stream_to_stdout=True,
                        )
                    except OllamaError as e:
                        print(f"\n  ERROR: {e}")
                        result = {
                            "text": "",
                            "model": model_name,
                            "model_digest": model_digest,
                            "tokens_per_second": 0.0,
                            "context_length": 0,
                            "status": "failed",
                        }

                    # Write output file
                    out_filename = _output_filename(
                        run_id, model_name, prompt_label,
                        corpus_label=corpus_label,
                        package_name=package_name,
                    )
                    out_path = _write_output(results_dir, out_filename, result["text"])

                    # Append to run log
                    log_entry = {
                        "id":                 run_id,
                        "timestamp":          datetime.datetime.now().isoformat(),
                        "experiment":         name,
                        "experiment_version": config.get("experiment", {}).get("experiment_version", 1),
                        "model":              result["model"],
                        "model_digest":       result["model_digest"],
                        "prompt_file":        str(prompt_dir / prompt_file),
                        "prompt_label":       prompt_label,
                        "package":            package_name,
                        "corpus_label":       corpus_label,
                        "output_file":        str(out_path),
                        "tokens_per_second":  result["tokens_per_second"],
                        "context_length":     result["context_length"],
                        "status":             result["status"],
                        "documented":         [],
                        "tags":               [],
                        "notes":              None,
                    }
                    _append_run_log(results_dir, log_entry)

                    print(f"\n  Written : {out_path}")
                    print(f"  Speed   : {result['tokens_per_second']} tok/s")
                    print(f"  Status  : {result['status']}")

        # Per-package confirmation pause (skipped if RUN_ALL)
        if package_name and not RUN_ALL:
            remaining = len(packages) - packages.index(package_name) - 1
            if remaining > 0:
                pkg_choice = _pause(
                    f"\n  {remaining} package(s) remaining. "
                    "Press ENTER to continue, 'a' for all, 's' to skip rest, 'q' to quit: "
                )
                if pkg_choice == "q":
                    print("Quitting.")
                    sys.exit(0)
                if pkg_choice == "s":
                    print("  Skipping remaining packages.")
                    break
                if pkg_choice == "a":
                    RUN_ALL = True

    return True
```

**Why:** The per-file block runs `return True` early so the packages loop
never executes when per-file mode is active. The modes are mutually exclusive
by the `elif` in the discovery block above and by this early return. The
packages loop is otherwise unchanged — no existing behavior is disrupted.
The `import subprocess` is local to `_run_pylint()` rather than top-level
because subprocess is only needed for this one experiment type.

---

## 2. experiments/02_linter_cleanup/config.yaml

**File path:** `experiments/02_linter_cleanup/config.yaml`

**BEFORE:**
```yaml
experiment:
  name: linter_cleanup
  description: >
    Run pylint against dev-utils Python source files, feed the report and
    source file to Gemma one file at a time, and ask it to fix the complaints.
    Tests mechanical code cleanup capability including docstring generation,
    whitespace fixes, line length, and unused import removal. Baseline pylint
    JSON captured before any changes; rerun after to measure improvement.
    Unused import removal is review_required — Gemma may remove imports that
    are actually needed.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils
  target_branch: ~               # works on current branch — no structural changes

model:
  temperature: 0.1               # minimum variation — mechanical fixes only

prompts:
  prompt_dir: prompts/
  prompts:
    - file: cleanup.md
      label: cleanup
      description: >
        Per-file cleanup instructions. Receives pylint report for the target
        file and full file contents via Jinja2 template variables.
        {{ target_file }} — file path
        {{ file_contents }} — full source
        {{ pylint_report }} — pylint JSON for this file only

results:
  results_dir: results/
  output: per_run

fix_categories:
  auto_fix:
    - missing docstrings
    - missing final newline
    - trailing whitespace
    - line length violations
  review_required:
    - unused imports              # Gemma may remove something actually needed
  out_of_scope:
    - max-args violations         # design complaint, not formatting
    - max-branches violations     # design complaint, not formatting
    - naming convention violations # rabbit hole, out of scope for this experiment
```

**AFTER:**
```yaml
experiment:
  name: linter_cleanup
  description: >
    Run pylint against dev-utils Python source files, feed the report and
    source file to Gemma one file at a time, and ask it to fix the complaints.
    Tests mechanical code cleanup capability including docstring generation,
    whitespace fixes, line length, and unused import removal. Baseline pylint
    JSON captured before any changes; rerun after to measure improvement.
    Unused import removal is review_required — Gemma may remove imports that
    are actually needed.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils
  target_branch: ~               # works on current branch — no structural changes

model:
  temperature: 0.1               # minimum variation — mechanical fixes only

prompts:
  prompt_dir: prompts/
  prompts:
    - file: cleanup.md
      label: cleanup
      description: >
        Per-file cleanup instructions. Receives pylint report for the target
        file and full file contents via Jinja2 template variables.
        {{ target_file }} — file path
        {{ file_contents }} — full source
        {{ pylint_report }} — pylint JSON for this file only

# =============================================================================
# repo_read
# Drives skeleton generation and per-file discovery.
# repo:      key from repos block in experiment_base.yaml / data config
# per_file:  true — iterate over Python files discovered from skeleton
# max_chars: not used for file content (files are read directly), but
#            retained for consistency with other experiments.
# =============================================================================

repo_read:
  repo: dev_utils
  per_file: true
  max_chars: 40000              # not used for file content — skeleton only

results:
  results_dir: results/
  output: per_run

fix_categories:
  auto_fix:
    - missing docstrings
    - missing final newline
    - trailing whitespace
    - line length violations
  review_required:
    - unused imports              # Gemma may remove something actually needed
  out_of_scope:
    - max-args violations         # design complaint, not formatting
    - max-branches violations     # design complaint, not formatting
    - naming convention violations # rabbit hole, out of scope for this experiment
```

**Why:** `repo_read` with `per_file: true` is all the runner needs to
discover files from the skeleton and enter per-file iteration mode.
The target repo (`dev_utils`) is the key from `experiment_base.yaml`'s
`repos` block — changing the target later is a one-line config edit here,
no code change.

---

## 3. pyproject.toml — add pylint to dev dependencies

**File path:** `pyproject.toml`

Find the `[project.optional-dependencies]` section (or `dev` extras block).

**BEFORE:**
```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-mock",
]
```

**AFTER:**
```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-mock",
    "pylint",
]
```

**Why:** Pylint must be available inside the container for `_run_pylint()`
to work. Adding it to dev dependencies ensures it's installed during
`pip install -e ".[dev]"` in the Dockerfile.

---

## After Applying

1. Rebuild the container: `podman-compose build`
2. Run experiment 02 — runner will print the list of discovered Python
   files, pause for confirmation, then iterate file by file
3. Each file produces output named e.g. `run_001_gemma4-e4b_cleanup_dbkit.txt`
4. Review output files — apply auto-fix category changes; human-verify
   unused import removals before applying

## Commit message

```
feat: add per-file iteration mode for linter_cleanup experiment
```
