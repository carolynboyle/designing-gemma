# =============================================================================
# designing_gemma/ollama_client.py
# Ollama API client. All model calls go through here.
# Streams responses to stdout and captures metrics for the run log.
# =============================================================================

import json
import time
from typing import Iterator

import requests


OLLAMA_BASE_URL = "http://localhost:11434"
GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"


class OllamaError(Exception):
    """Raised when the Ollama API returns an error or is unreachable."""


def check_connection() -> bool:
    """
    Verify Ollama is running and reachable.

    Returns:
        True if reachable, False otherwise.
    """
    try:
        response = requests.get(OLLAMA_BASE_URL, timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def _stream_response(response: requests.Response) -> Iterator[str]:
    """Yield decoded text tokens from a streaming Ollama response."""
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    break
            except json.JSONDecodeError:
                continue


def generate(
    model: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    digest: str | None = None,
    stream_to_stdout: bool = True,
) -> dict:
    """
    Send a prompt to Ollama and return the result with metrics.

    Args:
        model:             Ollama model name (e.g. 'gemma4:e2b')
        prompt:            Rendered prompt string
        temperature:       Sampling temperature
        max_tokens:        Maximum tokens to generate
        digest:            Optional pinned model digest for run log
        stream_to_stdout:  If True, print tokens to stdout as they arrive

    Returns:
        Dict with keys:
            text              — full generated text
            model             — model name used
            model_digest      — digest if provided, else None
            tokens_per_second — inference rate (float)
            context_length    — total tokens in context (int)
            status            — 'complete' or 'failed'

    Raises:
        OllamaError: If the API is unreachable or returns an error.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        response = requests.post(
            GENERATE_ENDPOINT,
            json=payload,
            stream=True,
            timeout=300,
        )
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Is it running?"
        ) from e

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama returned HTTP {response.status_code}: {response.text}"
        )

    full_text = []
    start_time = time.time()
    token_count = 0
    context_length = 0

    try:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            token = chunk.get("response", "")
            if token:
                full_text.append(token)
                token_count += 1
                if stream_to_stdout:
                    print(token, end="", flush=True)

            if chunk.get("done", False):
                context_length = chunk.get("context", 0)
                if isinstance(context_length, list):
                    context_length = len(context_length)
                break

    except requests.exceptions.ChunkedEncodingError as e:
        raise OllamaError(f"Stream interrupted: {e}") from e

    elapsed = time.time() - start_time
    tokens_per_second = round(token_count / elapsed, 2) if elapsed > 0 else 0.0

    if stream_to_stdout:
        print()  # newline after streamed output

    return {
        "text": "".join(full_text),
        "model": model,
        "model_digest": digest,
        "tokens_per_second": tokens_per_second,
        "context_length": context_length,
        "status": "complete",
    }
