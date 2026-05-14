# test_config.py

**Path:** tests/test_config.py
**Syntax:** python
**Generated:** 2026-05-13 22:16:06

```python
# =============================================================================
# tests/test_config.py
# Tests for designing_gemma.config
# =============================================================================

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from designing_gemma.config import (
    load_config,
    load_registry,
    enabled_experiments,
    _deep_merge,
    _enforce_staging,
)


# =============================================================================
# _deep_merge
# =============================================================================

class TestDeepMerge:

    def test_override_wins_on_scalar(self):
        base     = {"model": {"temperature": 0.2}}
        override = {"model": {"temperature": 0.5}}
        result   = _deep_merge(base, override)
        assert result["model"]["temperature"] == 0.5

    def test_base_key_preserved_when_not_overridden(self):
        base     = {"model": {"temperature": 0.2, "max_tokens": 2048}}
        override = {"model": {"temperature": 0.5}}
        result   = _deep_merge(base, override)
        assert result["model"]["max_tokens"] == 2048

    def test_nested_merge(self):
        base     = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 99}}}
        result   = _deep_merge(base, override)
        assert result["a"]["b"]["c"] == 99
        assert result["a"]["b"]["d"] == 2

    def test_override_adds_new_key(self):
        base     = {"a": 1}
        override = {"b": 2}
        result   = _deep_merge(base, override)
        assert result["a"] == 1
        assert result["b"] == 2

    def test_does_not_mutate_base(self):
        base     = {"model": {"temperature": 0.2}}
        override = {"model": {"temperature": 0.9}}
        _deep_merge(base, override)
        assert base["model"]["temperature"] == 0.2

    def test_does_not_mutate_override(self):
        base     = {"model": {"temperature": 0.2}}
        override = {"model": {"temperature": 0.9}}
        _deep_merge(base, override)
        assert override["model"]["temperature"] == 0.9

    def test_override_replaces_list(self):
        base     = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result   = _deep_merge(base, override)
        assert result["items"] == [4, 5]


# =============================================================================
# _enforce_staging
# =============================================================================

class TestEnforceStaging:

    def test_staging_forced_true(self):
        config = {"results": {"staging": False, "output": "per_run"}}
        result = _enforce_staging(config)
        assert result["results"]["staging"] is True

    def test_staging_remains_true(self):
        config = {"results": {"staging": True}}
        result = _enforce_staging(config)
        assert result["results"]["staging"] is True

    def test_no_results_key_is_safe(self):
        config = {"model": {"temperature": 0.2}}
        result = _enforce_staging(config)
        assert "results" not in result


# =============================================================================
# load_config
# =============================================================================

class TestLoadConfig:

    def test_loads_and_merges(self, tmp_path, base_config, experiment_config):
        with patch("designing_gemma.config.BASE_CONFIG_PATH", base_config):
            config = load_config(experiment_config)

        assert config["experiment"]["name"] == "test_experiment"
        assert config["model"]["max_tokens"] == 2048        # from base
        assert config["model"]["temperature"] == 0.3        # overridden by experiment

    def test_staging_always_true(self, tmp_path, base_config, experiment_config):
        # Write an experiment config that tries to override staging to False
        evil = {
            "experiment": {"name": "evil"},
            "results": {"staging": False},
        }
        evil_path = tmp_path / "evil_config.yaml"
        evil_path.write_text(yaml.dump(evil), encoding="utf-8")

        with patch("designing_gemma.config.BASE_CONFIG_PATH", base_config):
            config = load_config(evil_path)

        assert config["results"]["staging"] is True

    def test_missing_base_config_raises(self, tmp_path, experiment_config):
        with patch(
            "designing_gemma.config.BASE_CONFIG_PATH",
            tmp_path / "nonexistent.yaml"
        ):
            with pytest.raises(FileNotFoundError, match="Base config not found"):
                load_config(experiment_config)

    def test_missing_experiment_config_raises(self, tmp_path, base_config):
        with patch("designing_gemma.config.BASE_CONFIG_PATH", base_config):
            with pytest.raises(FileNotFoundError, match="Experiment config not found"):
                load_config(tmp_path / "nonexistent.yaml")


# =============================================================================
# load_registry
# =============================================================================

class TestLoadRegistry:

    def test_returns_list(self, registry_config):
        result = load_registry(registry_config)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_entry_fields_present(self, registry_config):
        result = load_registry(registry_config)
        entry = result[0]
        assert entry["number"] == "01"
        assert entry["name"] == "readme_gen"
        assert entry["enabled"] is True

    def test_missing_registry_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Registry not found"):
            load_registry(tmp_path / "nonexistent.yaml")


# =============================================================================
# enabled_experiments
# =============================================================================

class TestEnabledExperiments:

    def test_filters_disabled(self, registry_config):
        registry = load_registry(registry_config)
        result   = enabled_experiments(registry)
        names    = [e["name"] for e in result]
        assert "linter_cleanup" not in names
        assert "readme_gen" in names
        assert "pkg_restructure" in names

    def test_preserves_order(self, registry_config):
        registry = load_registry(registry_config)
        result   = enabled_experiments(registry)
        assert result[0]["number"] == "01"
        assert result[1]["number"] == "03"

    def test_empty_registry_returns_empty(self):
        assert enabled_experiments([]) == []

    def test_all_disabled_returns_empty(self):
        registry = [
            {"name": "a", "enabled": False},
            {"name": "b", "enabled": False},
        ]
        assert enabled_experiments(registry) == []

```
