# Changeset: num_ctx Context Window Override
## designing-gemma

Adds `num_ctx` as an optional per-experiment Ollama option. Motivated by
experiment 05 (srb_sentence_gen) where full corpora (1700-3000 words)
pushed prompts past the default 4096 token context window. Ollama
silently truncated the input; models never saw the source text.

Setting `num_ctx: 8192` in the experiment config doubles the window and
gives full corpora room to fit without truncation.

Default is `0` (not sent). When `0`, Ollama uses its own default (2048).
Only experiments that explicitly set `num_ctx` in their config will
send it to the API.

---

## 1. ollama_client.py — add num_ctx parameter

**File path:** `src/designing_gemma/ollama_client.py`

### 1a. Update `generate()` signature

**BEFORE:**
```python
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
```

**AFTER:**
```python
def generate(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    model: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    digest: str | None = None,
    stream_to_stdout: bool = True,
    repeat_penalty: float = 1.0,
    repeat_last_n: int = 64,
    num_ctx: int = 0,
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
        num_ctx:           Context window size in tokens (0 = use Ollama default)
```

**Why:** New optional parameter with a neutral default. Existing callers
are unaffected. When 0, the value is not sent to the API.

---

### 1b. Update payload to conditionally include num_ctx

**BEFORE:**
```python
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
```

**AFTER:**
```python
    options = {
        "temperature": temperature,
        "num_predict": max_tokens,
        "repeat_penalty": repeat_penalty,
        "repeat_last_n": repeat_last_n,
    }
    if num_ctx:
        options["num_ctx"] = num_ctx

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": options,
    }
```

**Why:** `num_ctx: 0` is not a meaningful Ollama value. Only send it
when explicitly set. Experiments that don't need a larger context window
get Ollama's default without any change in behavior.

---

## 2. experiment_runner.py — read num_ctx from config and pass to generate()

**File path:** `src/designing_gemma/experiment_runner.py`

### 2a. Read num_ctx from config

**BEFORE:**
```python
    temperature    = config.get("model", {}).get("temperature", 0.2)
    max_tokens     = config.get("model", {}).get("max_tokens", 2048)
    repeat_penalty = config.get("model", {}).get("repeat_penalty", 1.0)
    repeat_last_n  = config.get("model", {}).get("repeat_last_n", 64)
```

**AFTER:**
```python
    temperature    = config.get("model", {}).get("temperature", 0.2)
    max_tokens     = config.get("model", {}).get("max_tokens", 2048)
    repeat_penalty = config.get("model", {}).get("repeat_penalty", 1.0)
    repeat_last_n  = config.get("model", {}).get("repeat_last_n", 64)
    num_ctx        = config.get("model", {}).get("num_ctx", 0)
```

**Why:** Same pattern as repeat_penalty. Default of 0 means no override
for experiments that don't set it.

---

### 2b. Pass num_ctx to both generate() call sites

**BEFORE** (both call sites):
```python
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
```

**AFTER** (both call sites):
```python
                    result = generate(
                        model=model_name,
                        prompt=rendered_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        digest=model_digest,
                        stream_to_stdout=True,
                        repeat_penalty=repeat_penalty,
                        repeat_last_n=repeat_last_n,
                        num_ctx=num_ctx,
                    )
```

**Why:** Passes the config value through to the API. When 0, generate()
does not include it in the payload.

---

## 3. experiments/05_srb_sentence_gen/config.yaml — restore full corpora + add num_ctx

**Action:** Replace contents of `config.yaml` with the contents of
`config_full.yaml`, then add `num_ctx: 8192` to the `model:` block.
Rename the current test version to `config_test.yaml` for reference.

**File path:** `experiments/05_srb_sentence_gen/config.yaml`

**BEFORE** (model block — currently the test version has no model block):
```yaml
model:
  temperature: 0.3
```

**AFTER** (model block in the restored full config):
```yaml
model:
  temperature: 0.3               # slightly higher than mechanical tasks —
                                 # Gemma needs flexibility to interpret grammar
                                 # but output must still be structured SQL
  num_ctx: 8192                  # full corpora (1700-3000 words) + prompt
                                 # template + schema examples exceed the 4096
                                 # default. Confirmed by test run 2026-05-16.
```

**Why:** Context overflow confirmed by test run. At 4096 tokens Ollama
silently truncated the prompt and models never saw the source text. At
8192 the full corpus fits. The `num_ctx` annotation documents the
diagnosis for anyone reading the config later.

---

## After applying

1. Rename `experiments/05_srb_sentence_gen/config.yaml` →
   `experiments/05_srb_sentence_gen/config_test.yaml`
2. Rename `experiments/05_srb_sentence_gen/config_full.yaml` →
   `experiments/05_srb_sentence_gen/config.yaml`
3. Add `num_ctx: 8192` to the `model:` block of the new `config.yaml`
4. Apply changes to `ollama_client.py` and `experiment_runner.py`
5. Rebuild container: `podman-compose build`
6. Run experiment 05 — verify models extract sentences from full corpora

## Commit message

```
feat: add num_ctx context window override — fixes exp 05 corpus overflow
```
