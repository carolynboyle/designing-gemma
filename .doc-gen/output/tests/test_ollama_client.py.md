# test_ollama_client.py

**Path:** tests/test_ollama_client.py
**Syntax:** python
**Generated:** 2026-05-13 22:16:06

```python
# =============================================================================
# tests/test_ollama_client.py
# Tests for designing_gemma.ollama_client
# All Ollama API calls are mocked — no running Ollama instance required.
# =============================================================================

from unittest.mock import patch, MagicMock

import pytest
import requests

from designing_gemma.ollama_client import (
    check_connection,
    generate,
    OllamaError,
    OLLAMA_BASE_URL,
)


# =============================================================================
# check_connection
# =============================================================================

class TestCheckConnection:

    def test_returns_true_when_ollama_running(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("designing_gemma.ollama_client.requests.get", return_value=mock_resp):
            assert check_connection() is True

    def test_returns_false_when_ollama_not_running(self):
        with patch(
            "designing_gemma.ollama_client.requests.get",
            side_effect=requests.exceptions.ConnectionError,
        ):
            assert check_connection() is False

    def test_returns_false_on_non_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch("designing_gemma.ollama_client.requests.get", return_value=mock_resp):
            assert check_connection() is False


# =============================================================================
# generate
# =============================================================================

class TestGenerate:

    def test_returns_full_text(self, mock_ollama_response):
        mock_resp = mock_ollama_response(tokens=["Hello", " ", "world"])
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Say hello.",
                stream_to_stdout=False,
            )
        assert result["text"] == "Hello world"

    def test_status_is_complete_on_success(self, mock_ollama_response):
        mock_resp = mock_ollama_response()
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Test.",
                stream_to_stdout=False,
            )
        assert result["status"] == "complete"

    def test_model_name_in_result(self, mock_ollama_response):
        mock_resp = mock_ollama_response()
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e4b",
                prompt="Test.",
                stream_to_stdout=False,
            )
        assert result["model"] == "gemma4:e4b"

    def test_digest_passed_through(self, mock_ollama_response):
        mock_resp = mock_ollama_response()
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Test.",
                digest="sha256:abc123",
                stream_to_stdout=False,
            )
        assert result["model_digest"] == "sha256:abc123"

    def test_tokens_per_second_is_float(self, mock_ollama_response):
        mock_resp = mock_ollama_response()
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Test.",
                stream_to_stdout=False,
            )
        assert isinstance(result["tokens_per_second"], float)

    def test_context_length_captured(self, mock_ollama_response):
        mock_resp = mock_ollama_response(context_length=10)
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Test.",
                stream_to_stdout=False,
            )
        assert result["context_length"] == 10

    def test_raises_on_connection_error(self):
        with patch(
            "designing_gemma.ollama_client.requests.post",
            side_effect=requests.exceptions.ConnectionError,
        ):
            with pytest.raises(OllamaError, match="Cannot reach Ollama"):
                generate(
                    model="gemma4:e2b",
                    prompt="Test.",
                    stream_to_stdout=False,
                )

    def test_raises_on_non_200_response(self, mock_ollama_error_response):
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_ollama_error_response,
        ):
            with pytest.raises(OllamaError, match="HTTP 500"):
                generate(
                    model="gemma4:e2b",
                    prompt="Test.",
                    stream_to_stdout=False,
                )

    def test_empty_tokens_returns_empty_text(self, mock_ollama_response):
        mock_resp = mock_ollama_response(tokens=[])
        with patch(
            "designing_gemma.ollama_client.requests.post",
            return_value=mock_resp,
        ):
            result = generate(
                model="gemma4:e2b",
                prompt="Test.",
                stream_to_stdout=False,
            )
        assert result["text"] == ""

```
