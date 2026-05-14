# conftest.py

**Path:** tests/conftest.py
**Syntax:** python
**Generated:** 2026-05-13 22:16:06

```python
# =============================================================================
# tests/conftest.py
# Shared pytest fixtures for designing-gemma test suite.
# =============================================================================

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml


# =============================================================================
# Config fixtures
# =============================================================================

@pytest.fixture
def base_config(tmp_path):
    """Write a minimal experiment_base.yaml to tmp_path and return its path."""
    config = {
        "experiment": {
            "name": None,
            "description": None,
            "experiment_version": 1,
            "target_repo": None,
            "target_branch": None,
        },
        "model": {
            "models": [
                {"name": "gemma4:e2b", "digest": None},
                {"name": "gemma4:e4b", "digest": None},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        },
        "prompts": {
            "prompt_dir": "prompts/",
            "prompts": [],
        },
        "results": {
            "results_dir": "results/",
            "output": "per_run",
            "staging": True,
        },
        "run_log": {
            "log_file": "run_log.yaml",
            "documented": [],
        },
        "fix_categories": {
            "auto_fix": [],
            "review_required": [],
            "out_of_scope": [],
        },
    }
    path = tmp_path / "experiment_base.yaml"
    path.write_text(yaml.dump(config), encoding="utf-8")
    return path


@pytest.fixture
def experiment_config(tmp_path):
    """Write a minimal experiment config.yaml to tmp_path and return its path."""
    config = {
        "experiment": {
            "name": "test_experiment",
            "description": "A test experiment.",
            "experiment_version": 1,
            "target_repo": "https://github.com/carolynboyle/test-repo",
        },
        "model": {
            "temperature": 0.3,
        },
        "prompts": {
            "prompt_dir": "prompts/",
            "prompts": [
                {"file": "test_prompt.md", "label": "test"},
            ],
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config), encoding="utf-8")
    return path


@pytest.fixture
def registry_config(tmp_path):
    """Write a minimal experiments.yaml registry to tmp_path and return its path."""
    registry = {
        "experiments": [
            {
                "number": "01",
                "name": "readme_gen",
                "risk": "none",
                "depends_on": [],
                "enabled": True,
                "config": "experiments/01_readme_gen/config.yaml",
                "notes": "Test experiment one.",
            },
            {
                "number": "02",
                "name": "linter_cleanup",
                "risk": "low",
                "depends_on": [],
                "enabled": False,
                "config": "experiments/02_linter_cleanup/config.yaml",
                "notes": "Test experiment two — disabled.",
            },
            {
                "number": "03",
                "name": "pkg_restructure",
                "risk": "high",
                "depends_on": [],
                "enabled": True,
                "config": "experiments/03_pkg_restructure/config.yaml",
                "notes": "Test experiment three.",
            },
        ]
    }
    path = tmp_path / "experiments.yaml"
    path.write_text(yaml.dump(registry), encoding="utf-8")
    return path


# =============================================================================
# Prompt fixtures
# =============================================================================

@pytest.fixture
def prompt_dir(tmp_path):
    """Create a prompts/ directory in tmp_path with a test prompt file."""
    p = tmp_path / "prompts"
    p.mkdir()
    prompt = p / "test_prompt.md"
    prompt.write_text(
        "Hello, {{ name }}. The answer is {{ answer }}.",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def prompt_dir_no_vars(tmp_path):
    """Create a prompts/ directory with a prompt that has no template variables."""
    p = tmp_path / "prompts"
    p.mkdir()
    prompt = p / "simple.md"
    prompt.write_text(
        "This prompt has no variables.",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def corpus_file(tmp_path):
    """Write a small corpus text file to tmp_path and return its path."""
    path = tmp_path / "corpus.txt"
    path.write_text(
        "The ships hung in the sky in much the same way that bricks don't.",
        encoding="utf-8",
    )
    return path


# =============================================================================
# Ollama mock fixtures
# =============================================================================

@pytest.fixture
def mock_ollama_response():
    """
    Return a factory that builds a mock requests.Response for Ollama streaming.
    Usage: mock_ollama_response(tokens=["Hello", " world"])
    """
    def _make_response(tokens=None, done=True, context_length=42):
        if tokens is None:
            tokens = ["Hello", " ", "world"]
        lines = []
        for i, token in enumerate(tokens):
            is_last = (i == len(tokens) - 1) and done
            chunk = {"response": token, "done": is_last}
            if is_last:
                chunk["context"] = list(range(context_length))
            lines.append(json.dumps(chunk).encode("utf-8"))

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = iter(lines)
        return mock_resp

    return _make_response


@pytest.fixture
def mock_ollama_error_response():
    """Return a mock requests.Response with a non-200 status code."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    return mock_resp

```
