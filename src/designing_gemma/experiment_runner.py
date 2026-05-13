# =============================================================================
# designing_gemma/experiment_runner.py
# Orchestrates experiment runs end-to-end.
# Interactive CLI — pauses between experiments for human review.
# Entry point: designing-gemma (see pyproject.toml)
# =============================================================================

import sys
import datetime
from pathlib import Path

import yaml

from designing_gemma import __version__
from designing_gemma.config import load_config, load_registry, enabled_experiments
from designing_gemma.ollama_client import generate, check_connection, OllamaError
from designing_gemma.prompt_loader import load_prompt, load_corpus, PromptError


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


# =============================================================================
# Output file
# =============================================================================

def _output_filename(
    run_id: str,
    model: str,
    prompt_label: str,
    corpus_label: str | None = None,
) -> str:
    """Build a result filename from run metadata."""
    model_slug = model.replace(":", "-").replace("/", "-")
    parts = [run_id, model_slug, prompt_label]
    if corpus_label:
        parts.append(corpus_label)
    return "_".join(parts) + ".txt"


def _write_output(results_dir: Path, filename: str, text: str) -> Path:
    """Write generated output to results dir. Returns the output path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / filename
    out_path.write_text(text, encoding="utf-8")
    return out_path


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
    name   = experiment_entry.get("name", "unknown")
    number = experiment_entry.get("number", "??")
    risk   = experiment_entry.get("risk", "unknown")
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

    for prompt_def in prompts:
        prompt_file  = prompt_def.get("file")
        prompt_label = prompt_def.get("label", prompt_file)

        for corpus in corpus_list:
            corpus_label = corpus["label"] if corpus else None

             # Build Jinja2 context — start from base, add corpus if present
            context = dict(base_context)
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
                    run_id, model_name, prompt_label, corpus_label
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

    return True


# =============================================================================
# Main entry point
# =============================================================================

def main() -> None:
    """Entry point for the designing-gemma CLI."""

    _header(f"Designing Gemma  v{__version__}")
    print("  A structured experiment framework for local LLM evaluation.")
    print("  Don't Panic.")

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
    print()


if __name__ == "__main__":
    main()
