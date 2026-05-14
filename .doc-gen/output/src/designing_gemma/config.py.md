# config.py

**Path:** src/designing_gemma/config.py
**Syntax:** python
**Generated:** 2026-05-13 22:16:06

```python
# =============================================================================
# designing_gemma/config.py
# Loads and merges experiment_base.yaml with an experiment's config.yaml.
# Experiment config wins on all conflicts.
# =============================================================================

import copy
from pathlib import Path

import yaml


BASE_CONFIG_PATH = Path("data/experiment_base.yaml")


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins on all conflicts."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _enforce_staging(config: dict) -> dict:
    """Ensure results.staging is always true. This field may not be overridden."""
    if "results" in config:
        config["results"]["staging"] = True
    return config


def load_config(experiment_config_path: str | Path) -> dict:
    """
    Load and merge experiment_base.yaml with the given experiment config.

    Args:
        experiment_config_path: Path to the experiment's config.yaml

    Returns:
        Merged config dict. Experiment values override base values.
        results.staging is always forced to True regardless of override attempts.

    Raises:
        FileNotFoundError: If either config file does not exist.
        yaml.YAMLError: If either file contains invalid YAML.
    """
    base_path = BASE_CONFIG_PATH
    experiment_path = Path(experiment_config_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Base config not found: {base_path}")
    if not experiment_path.exists():
        raise FileNotFoundError(f"Experiment config not found: {experiment_path}")

    with base_path.open("r", encoding="utf-8") as f:
        base = yaml.safe_load(f) or {}

    with experiment_path.open("r", encoding="utf-8") as f:
        experiment = yaml.safe_load(f) or {}

    merged = _deep_merge(base, experiment)
    merged = _enforce_staging(merged)

    return merged


def load_registry(registry_path: str | Path = "data/experiments.yaml") -> list[dict]:
    """
    Load the master experiment registry.

    Args:
        registry_path: Path to experiments.yaml

    Returns:
        List of experiment registry entries, in run order.

    Raises:
        FileNotFoundError: If the registry file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    path = Path(registry_path)
    if not path.exists():
        raise FileNotFoundError(f"Registry not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("experiments", [])


def enabled_experiments(registry: list[dict]) -> list[dict]:
    """Return only experiments with enabled: true, in registry order."""
    return [e for e in registry if e.get("enabled", False)]

```
