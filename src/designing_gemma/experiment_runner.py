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

from designing_gemma import __version__
from designing_gemma.config import load_config, load_registry, enabled_experiments
from designing_gemma.ollama_client import generate, check_connection, OllamaError
from designing_gemma.prompt_loader import load_prompt, load_corpus, PromptError
from designing_gemma.repo_reader import read_repo_context, RepoReaderError
from designing_gemma.skeleton_reader import build_skeleton, SkeletonError
from designing_gemma.manifest_filter import filter_manifest, ManifestFilterError


# =============================================================================
# Global flags
# =============================================================================

# Set to True when user chooses "run all" at the per-package confirmation prompt.
# When True, per-package pauses are skipped and runs proceed automatically.
RUN_ALL = False

# Session log path — project root, overwritten every run.
# Rename to keep: e.g. session_log_2026-05-14.txt
SESSION_LOG_PATH = "session_log.txt"


# =============================================================================
# Session logger
# =============================================================================

# ANSI escape code pattern — stripped before writing to log file.
_ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


class SessionLogger(io.TextIOBase):
    """
    Tee wrapper for stdout — writes to both terminal and session_log.txt.

    Installed at the start of main() via sys.stdout replacement.
    Strips ANSI color codes before writing to the log file so the file
    is clean text rather than escape sequences.

    The log file is opened once at construction and closed on restore().
    Overwrites any existing session_log.txt from a previous run — rename
    the file before running if you want to keep the previous session.
    """

    def __init__(self, log_path: Path, terminal: io.TextIOBase):
        self._terminal = terminal
        self._log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file = log_path.open("w", encoding="utf-8")
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        self._log_file.write("# session_log.txt — designing-gemma\n")
        self._log_file.write(f"# Started : {timestamp}\n")
        self._log_file.write("# Rename this file to keep it — overwritten on next run.\n\n")
        self._log_file.flush()

    def write(self, text: str) -> int:
        self._terminal.write(text)
        self._terminal.flush()
        clean = _ANSI_ESCAPE.sub("", text)
        self._log_file.write(clean)
        self._log_file.flush()
        return len(text)

    def flush(self) -> None:
        self._terminal.flush()
        self._log_file.flush()

    def restore(self) -> None:
        """Restore original stdout and close the log file."""
        sys.stdout = self._terminal
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        self._log_file.write(f"\n# Ended : {timestamp}\n")
        self._log_file.flush()
        self._log_file.close()


# =============================================================================
# Formatting helpers
# =============================================================================

RISK_COLORS = {
    "none":   "\033[32m",   # green
    "low":    "\033[33m",   # yellow
    "medium": "\033[33m",   # yellow
    "high":   "\033[31m",   # red
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def _risk_label(risk: str) -> str:
    color = RISK_COLORS.get(risk.lower(), "")
    return f"{color}{risk.upper()}{RESET}"


def _header(text: str) -> None:
    width = 70
    print()
    print("=" * width)
    print(f"  {BOLD}{text}{RESET}")
    print("=" * width)


def _subheader(text: str) -> None:
    print(f"\n--- {text} ---")


def _pause(prompt: str = "") -> str:
    """
    Pause and wait for user input.
    Returns the stripped input string.
    """
    try:
        return input(prompt).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted.")
        sys.exit(0)


# =============================================================================
# Run log
# =============================================================================

def _run_id(results_dir: Path) -> str:
    """Generate a sequential run ID based on existing run_log.yaml entries."""
    log_path = results_dir / "run_log.yaml"
    if not log_path.exists():
        return "run_001"
    with log_path.open("r", encoding="utf-8") as f:
        log = yaml.safe_load(f) or []
    return f"run_{len(log) + 1:03d}"


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


# =============================================================================
# Output file
# =============================================================================

def _output_filename(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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


def _write_output(results_dir: Path, filename: str, text: str) -> Path:
    """Write generated output to results dir. Returns the output path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / filename
    out_path.write_text(text, encoding="utf-8")
    return out_path


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

    Records exactly what was injected as {{ repo_context }} for this run.
    Overwritten on every run — always reflects the most recent build.

    Args:
        results_dir:   Experiment results directory.
        context_text:  The formatted repo context string.
        repo_key:      Repo identifier from config (e.g. "dev_utils").
        manifest_path: Manifest path used for skeleton build.
        truncated:     Whether the context was truncated at the char limit.
        package_name:  Package name if running per-package, else None.
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
        if package_name:
            f.write(f"# Package   : {package_name}\n")
        f.write(f"# Chars     : {char_count:,}\n")
        f.write(f"# Truncated : {truncated}\n")
        f.write("#\n")
        f.write(context_text)


# =============================================================================
# Package and file discovery
# =============================================================================

def _discover_packages(skeleton_data: dict) -> list[str]:
    """
    Discover Python packages from skeleton data.

    A package is any directory under python/ that contains a pyproject.toml.
    Returns a sorted list of package names (the directory name only, not
    the full path).

    Args:
        skeleton_data: Output of build_skeleton().

    Returns:
        Sorted list of package name strings, e.g. ["dbkit", "fletcher", ...]
    """
    packages = set()
    for entry in skeleton_data.get("files", []):
        path = entry.get("path", "")
        parts = Path(path).parts
        if (
            len(parts) == 3
            and parts[0] == "python"
            and parts[2] == "pyproject.toml"
        ):
            packages.add(parts[1])
    return sorted(packages)


def _filter_skeleton_for_package(
    skeleton_data: dict,
    package_name: str,
) -> dict:
    """
    Return a copy of skeleton_data containing only files for one package.

    Filters to entries whose path starts with python/<package_name>/.
    Preserves the stats and generated keys from the original.

    Args:
        skeleton_data: Output of build_skeleton().
        package_name:  Package directory name, e.g. "fletcher".

    Returns:
        Filtered skeleton dict suitable for passing to read_repo_context().
    """
    prefix = f"python/{package_name}/"
    filtered_files = [
        entry for entry in skeleton_data.get("files", [])
        if entry.get("path", "").startswith(prefix)
    ]
    return {
        "files":     filtered_files,
        "stats":     skeleton_data.get("stats", {}),
        "generated": skeleton_data.get("generated", ""),
    }


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
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", str(abs_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
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

def _run_experiment(experiment_entry: dict) -> bool:
    """
    Run a single experiment interactively.

    Args:
        experiment_entry: Registry entry dict for the experiment.

    Returns:
        True if the experiment completed (even partially),
        False if the user skipped it.
    """
    global RUN_ALL  # pylint: disable=global-statement

    name        = experiment_entry.get("name", "unknown")
    number      = experiment_entry.get("number", "??")
    risk        = experiment_entry.get("risk", "unknown")
    config_path = experiment_entry.get("config", "")

    _header(f"Experiment {number}: {name}  [risk: {_risk_label(risk)}]")

    # Load merged config
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"  ERROR: {e}")
        return False

    experiment_dir = Path(config_path).parent
    results_dir    = experiment_dir / config.get("results", {}).get("results_dir", "results/")
    prompt_dir     = experiment_dir / config.get("prompts", {}).get("prompt_dir", "prompts/")
    prompts        = config.get("prompts", {}).get("prompts", [])
    models         = config.get("model", {}).get("models", [])
    temperature    = config.get("model", {}).get("temperature", 0.2)
    max_tokens     = config.get("model", {}).get("max_tokens", 2048)
    repeat_penalty = config.get("model", {}).get("repeat_penalty", 1.0)
    repeat_last_n  = config.get("model", {}).get("repeat_last_n", 64)
    repeat_penalty = config.get("model", {}).get("repeat_penalty", 1.0)
    repeat_last_n  = config.get("model", {}).get("repeat_last_n", 64)
    corpora        = config.get("corpora", None)

    description = config.get("experiment", {}).get("description", "")
    if description:
        print(f"\n  {description.strip()}")

    print(f"\n  Prompts : {[p['label'] for p in prompts]}")
    print(f"  Models  : {[m['name'] for m in models]}")
    if corpora:
        active = [c["label"] for c in corpora if c.get("status") == "active"]
        print(f"  Corpora : {active}")

    choice = _pause("\nPress ENTER to run, 's' to skip, 'q' to quit: ")
    if choice == "q":
        print("Quitting.")
        sys.exit(0)
    if choice == "s":
        print(f"  Skipped {name}.")
        return False

    # Build prompt × model × corpus combinations
    corpus_list = (
        [c for c in corpora if c.get("status") == "active"]
        if corpora
        else [None]
    )

    # Build base context — available to all prompts in this experiment
    repos = config.get("repos", {})
    base_context = {"repos": repos} if repos else {}

    # Inject run_log if experiment requests it
    if config.get("inject_run_log", False):
        run_log_text = _load_run_log(results_dir)
        if run_log_text:
            base_context["run_log"] = run_log_text
            print(f"  Run log injected ({len(run_log_text):,} chars)")
        else:
            print("  WARNING: inject_run_log requested but no run_log.yaml found")

    # Load repo context if experiment specifies repo_read
    repo_read     = config.get("repo_read")
    skeleton_data = None
    max_chars     = 40_000

    if repo_read:
        repo_key       = repo_read.get("repo")
        repo_root      = Path(repos.get(repo_key, ""))
        max_chars      = repo_read.get("max_chars", max_chars)
        size_overrides = repo_read.get("size_overrides") or None
        manifest_path  = repo_read.get("manifest", ".doc-gen/manifest.yml")

        try:
            manifest_filter_cfg = repo_read.get("manifest_filter")
            if manifest_filter_cfg:
                filter_manifest(
                    repo_root,
                    include_prefixes=manifest_filter_cfg.get("include", []),
                    source_manifest=manifest_filter_cfg.get("source", ".doc-gen/manifest.yml"),
                    output_manifest=manifest_path,
                )
            skeleton_data = build_skeleton(
                repo_root,
                manifest_path=manifest_path,
                size_overrides=size_overrides,
            )
        except (SkeletonError, ManifestFilterError) as e:
            print(f"  ERROR building skeleton: {e}")
            return False

    # Determine iteration mode — per-package, per-file, or single pass
    packages       = []
    py_files       = []
    repo_root_path = Path()

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
            print(
                "  WARNING: no packages found in skeleton data"
                " — running without per-package iteration."
            )

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
            print(
                "  WARNING: no Python files found in skeleton data"
                " — running without per-file iteration."
            )

    # If no packages or files discovered (or neither mode set), run as single pass
    if not packages:
        packages = [None]

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
                context["target_file"]   = rel_path
                context["file_contents"] = file_contents
                context["pylint_report"] = pylint_report

                try:
                    rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
                except PromptError as e:
                    print(f"  ERROR rendering prompt {prompt_file}: {e}")
                    continue

                for model_def in models:
                    model_name   = model_def.get("name")
                    model_digest = model_def.get("digest")

                    run_id = _run_id(results_dir)

                    _subheader(f"{prompt_label} / {file_stem} / {model_name}")


                    try:
                        result = generate(
                            model=model_name,
                            prompt=rendered_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            digest=model_digest,
                            stream_to_stdout=True,
                            repeat_penalty=repeat_penalty,
                            repeat_last_n=repeat_last_n,
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
                        "experiment_version": (
                            config.get("experiment", {}).get("experiment_version", 1)
                        ),
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
                    if result["status"] == "bailed":
                        print(f"  Status  : {result['status']} "
                              f"⚠️  model emitted 0 tokens — silent bail")
                    else:
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
            pkg_num = packages.index(package_name) + 1
            _subheader(f"Package: {package_name}  ({pkg_num}/{len(packages)})")

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
                    print(
                        f"  WARNING: repo context truncated"
                        f" — {result['files_excluded']} file(s) omitted"
                    )
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
                            repeat_penalty=repeat_penalty,
                            repeat_last_n=repeat_last_n,
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
                        "experiment_version": (
                            config.get("experiment", {}).get("experiment_version", 1)
                        ),
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


# =============================================================================
# Main entry point
# =============================================================================

def main() -> None:
    """Entry point for the designing-gemma CLI."""

    # Install session logger — tees stdout to session_log.txt
    log_path = Path(SESSION_LOG_PATH)
    logger = SessionLogger(log_path, sys.stdout)
    sys.stdout = logger

    try:
        _header(f"Designing Gemma  v{__version__}")
        print("  A structured experiment framework for local LLM evaluation.")
        print("  Don't Panic.")
        print(f"\n  Session log: {log_path.resolve()}")

        # Check Ollama connection before doing anything else
        print("\nChecking Ollama connection...")
        if not check_connection():
            print(
                "  ERROR: Cannot reach Ollama at http://localhost:11434\n"
                "  Make sure Ollama is running: ollama serve\n"
            )
            sys.exit(1)
        print("  Ollama is running.")

        # Load registry
        try:
            registry = load_registry()
        except FileNotFoundError as e:
            print(f"\n  ERROR: {e}")
            sys.exit(1)

        experiments = enabled_experiments(registry)

        if not experiments:
            print("\n  No enabled experiments found in data/experiments.yaml.")
            sys.exit(0)

        print(f"\n  {len(experiments)} experiment(s) enabled:\n")
        for exp in experiments:
            risk_str = _risk_label(exp.get("risk", "unknown"))
            print(f"    {exp['number']}  {exp['name']:<25} risk: {risk_str}")

        _pause("\nPress ENTER to begin, 'q' to quit: ")

        completed = []
        skipped   = []

        for exp in experiments:
            ran = _run_experiment(exp)
            if ran:
                completed.append(exp["name"])
            else:
                skipped.append(exp["name"])

        _header("Run complete")
        print(f"  Completed : {completed or 'none'}")
        print(f"  Skipped   : {skipped or 'none'}")
        print(f"  Log saved : {log_path.resolve()}")
        print()

    finally:
        logger.restore()


if __name__ == "__main__":
    main()
