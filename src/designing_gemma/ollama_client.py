# =============================================================================
# designing_gemma/ollama_client.py
# Ollama API client. All model calls go through here.
# Streams responses to stdout and captures metrics for the run log.
# =============================================================================
"""
Ollama API client for the designing-gemma experiment framework.

All model calls go through here. Handles streaming, metrics capture,
repeat penalty options, and bail detection via eval_count.
"""

import json
import os
import time
from typing import Iterator

import requests



OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
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


def generate(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    model: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    digest: str | None = None,
    stream_to_stdout: bool = True,
    repeat_penalty: float = 1.0,
    repeat_last_n: int = 64,
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
        repeat_penalty:    Repetition penalty (1.0 = disabled, 1.3 = moderate)
        repeat_last_n:     Token window for repetition penalty (0 = disabled)

    Returns:
        Dict with keys:
            text              — full generated text
            model             — model name used
            model_digest      — digest if provided, else None
            tokens_per_second — inference rate (float)
            context_length    — total tokens in context (int)
            eval_count        — tokens generated (0 = model bailed immediately)
            status            — 'complete', 'bailed', or 'failed'

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
            "repeat_penalty": repeat_penalty,
            "repeat_last_n": repeat_last_n,
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
    eval_count = 0

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
                eval_count = chunk.get("eval_count", token_count)
                break

    except requests.exceptions.ChunkedEncodingError as e:
        raise OllamaError(f"Stream interrupted: {e}") from e

    elapsed = time.time() - start_time
    tokens_per_second = round(token_count / elapsed, 2) if elapsed > 0 else 0.0

    if stream_to_stdout:
        print()  # newline after streamed output

    status = "bailed" if eval_count == 0 else "complete"

    return {
        "text": "".join(full_text),
        "model": model,
        "model_digest": digest,
        "tokens_per_second": tokens_per_second,
        "context_length": context_length,
        "eval_count": eval_count,
        "status": status,
    }
