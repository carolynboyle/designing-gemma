# test_prompt_loader.py

**Path:** tests/test_prompt_loader.py
**Syntax:** python
**Generated:** 2026-05-13 07:45:45

```python
# =============================================================================
# tests/test_prompt_loader.py
# Tests for designing_gemma.prompt_loader
# =============================================================================

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import requests

from designing_gemma.prompt_loader import load_prompt, load_corpus, PromptError


# =============================================================================
# load_prompt
# =============================================================================

class TestLoadPrompt:

    def test_renders_template_variables(self, prompt_dir):
        result = load_prompt(
            "test_prompt.md",
            prompt_dir,
            context={"name": "Gemma", "answer": 42},
        )
        assert result == "Hello, Gemma. The answer is 42."

    def test_renders_without_variables(self, prompt_dir_no_vars):
        result = load_prompt("simple.md", prompt_dir_no_vars, context={})
        assert result == "This prompt has no variables."

    def test_none_context_treated_as_empty(self, prompt_dir_no_vars):
        result = load_prompt("simple.md", prompt_dir_no_vars, context=None)
        assert result == "This prompt has no variables."

    def test_missing_variable_raises(self, prompt_dir):
        with pytest.raises(PromptError, match="Failed to render"):
            load_prompt(
                "test_prompt.md",
                prompt_dir,
                context={"name": "Gemma"},   # missing 'answer'
            )

    def test_missing_prompt_file_raises(self, prompt_dir):
        with pytest.raises(PromptError, match="Prompt file not found"):
            load_prompt("nonexistent.md", prompt_dir, context={})

    def test_missing_prompt_dir_raises(self, tmp_path):
        with pytest.raises(PromptError, match="Prompt directory not found"):
            load_prompt(
                "test_prompt.md",
                tmp_path / "nonexistent_dir",
                context={},
            )

    def test_returns_string(self, prompt_dir_no_vars):
        result = load_prompt("simple.md", prompt_dir_no_vars)
        assert isinstance(result, str)

    def test_accepts_pathlib_prompt_dir(self, prompt_dir):
        result = load_prompt(
            "test_prompt.md",
            Path(prompt_dir),
            context={"name": "Gemma", "answer": 42},
        )
        assert "Gemma" in result


# =============================================================================
# load_corpus — file
# =============================================================================

class TestLoadCorpusFile:

    def test_loads_file_content(self, corpus_file):
        result = load_corpus(str(corpus_file), "file")
        assert "bricks" in result

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(PromptError, match="Corpus file not found"):
            load_corpus(str(tmp_path / "nonexistent.txt"), "file")

    def test_returns_string(self, corpus_file):
        result = load_corpus(str(corpus_file), "file")
        assert isinstance(result, str)


# =============================================================================
# load_corpus — url
# =============================================================================

class TestLoadCorpusUrl:

    def test_fetches_url_content(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Far out in the uncharted backwaters of the galaxy..."
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_resp):
            result = load_corpus("https://example.com/corpus.txt", "url")

        assert "uncharted backwaters" in result

    def test_url_fetch_failure_raises(self):
        with patch(
            "requests.get",
            side_effect=requests.exceptions.ConnectionError("unreachable"),
        ):
            with pytest.raises(PromptError, match="Failed to fetch corpus"):
                load_corpus("https://example.com/corpus.txt", "url")

    def test_http_error_raises(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(PromptError, match="Failed to fetch corpus"):
                load_corpus("https://example.com/corpus.txt", "url")


# =============================================================================
# load_corpus — invalid source_type
# =============================================================================

class TestLoadCorpusInvalidType:

    def test_unknown_source_type_raises(self, corpus_file):
        with pytest.raises(ValueError, match="Unknown source_type"):
            load_corpus(str(corpus_file), "ftp")

```
