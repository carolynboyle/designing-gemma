# Changeset: Repeat Penalty Config + eval_count Capture
## designing-gemma

Two related improvements motivated by the linter_cleanup experiment findings:

1. **Repeat penalty** — adds `repeat_penalty` and `repeat_last_n` as
   optional config-driven model options, passed through to the Ollama API.
   Intended to break e2b's looping failure mode on incomplete code.

2. **eval_count capture** — captures `eval_count` from Ollama's done chunk
   and returns it in the result dict. Runner uses it to set status `"bailed"`
   when the model emits 0 tokens, giving the run log an accurate signal
   instead of falsely reporting `"complete"`.

Both changes follow existing patterns — config-driven, no hardcoded values,
run log accurately reflects what happened.

---

## 1. experiment_base.yaml — add repeat penalty defaults

**File path:** `data/experiment_base.yaml`

**BEFORE:**
```yaml
model:
  models:                        # run experiment against each model in list
    - name: gemma4:e2b
      digest: ~
    - name: gemma4:e4b
      digest: ~
  temperature: 0.2
  max_tokens: 2048
```

**AFTER:**
```yaml
model:
  models:                        # run experiment against each model in list
    - name: gemma4:e2b
      digest: ~
    - name: gemma4:e4b
      digest: ~
  temperature: 0.2
  max_tokens: 2048
  repeat_penalty: 1.0            # 1.0 = disabled (Ollama default)
                                 # raise to 1.2–1.5 to break repetition loops
  repeat_last_n: 64              # token window the penalty looks back on
                                 # 64 is a reasonable default; 0 disables
```

**Why:** Establishes the fields with neutral defaults so all experiments
inherit them without changing behavior. Individual experiments override
to activate the penalty. Config-driven, not hardcoded.

---

## 2. experiments/02_linter_cleanup/config.yaml — activate penalty

**File path:** `experiments/02_linter_cleanup/config.yaml`

**BEFORE:**
```yaml
model:
  temperature: 0.1               # minimum variation — mechanical fixes only
```

**AFTER:**
```yaml
model:
  temperature: 0.1               # minimum variation — mechanical fixes only
  max_tokens: 800                # linter fixes don't need 2048 tokens;
                                 # tight ceiling catches loops early
  repeat_penalty: 1.3            # penalise repetition — breaks e2b loop mode
  repeat_last_n: 64              # look back 64 tokens when applying penalty
```

**Why:** `max_tokens` dropped from 2048 to 800 — a complete fixed file
for a typical dev-utils module shouldn't exceed this. Tight ceiling means
loops hit the token limit quickly rather than running to 2048. `repeat_penalty`
of 1.3 is the midpoint of Gemini's suggested 1.2–1.5 range — conservative
enough not to distort valid output, aggressive enough to break simple loops.

---

## 3. ollama_client.py — add repeat penalty params + eval_count capture

**File path:** `src/designing_gemma/ollama_client.py`

### 3a. Update `generate()` signature

**BEFORE:**
```python
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
```

**AFTER:**
```python
def generate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
```

**Why:** Two new optional parameters with neutral defaults — existing callers
are unaffected. `pylint: disable` added because 8 parameters is intentional
(each is a distinct Ollama API option).

---

### 3b. Update payload to include repeat penalty options

**BEFORE:**
```python
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
```

**AFTER:**
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

**Why:** Passes the new parameters to the Ollama API. When `repeat_penalty`
is 1.0 (the default), Ollama treats it as disabled — no behavior change for
experiments that don't set it.

---

### 3c. Capture eval_count from done chunk

**BEFORE:**
```python
            if chunk.get("done", False):
                context_length = chunk.get("context", 0)
                if isinstance(context_length, list):
                    context_length = len(context_length)
                break
```

**AFTER:**
```python
            if chunk.get("done", False):
                context_length = chunk.get("context", 0)
                if isinstance(context_length, list):
                    context_length = len(context_length)
                eval_count = chunk.get("eval_count", token_count)
                break
```

**Why:** `eval_count` is the number of tokens the model actually generated,
as reported by Ollama in the final done chunk. When the model bails
immediately (silent e2b failure mode), `eval_count` is 0. Falling back to
`token_count` when absent ensures backward compatibility.

---

### 3d. Initialize eval_count and update status logic in return

**BEFORE:**
```python
    full_text = []
    start_time = time.time()
    token_count = 0
    context_length = 0
```

**AFTER:**
```python
    full_text = []
    start_time = time.time()
    token_count = 0
    context_length = 0
    eval_count = 0
```

And update the return dict:

**BEFORE:**
```python
    return {
        "text": "".join(full_text),
        "model": model,
        "model_digest": digest,
        "tokens_per_second": tokens_per_second,
        "context_length": context_length,
        "status": "complete",
    }
```

**AFTER:**
```python
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
```

**Why:** `eval_count == 0` is the definitive signal that the model emitted
an immediate EOS token — the "silent bail" failure mode observed in e2b.
Reporting this as `"bailed"` rather than `"complete"` makes the run log
accurate and gives the post-run review a clean filter: any result with
`status: bailed` is a file the model couldn't handle.

---

## 4. experiment_runner.py — pass repeat penalty to generate()

**File path:** `src/designing_gemma/experiment_runner.py`

Both the per-file and per-package loops call `generate()`. Both need the
new parameters passed through from config.

**BEFORE** (appears twice — once in per-file loop, once in per-package loop):
```python
                    try:
                        result = generate(
                            model=model_name,
                            prompt=rendered_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            digest=model_digest,
                            stream_to_stdout=True,
                        )
```

**AFTER** (both occurrences):
```python
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
```

And add the config reads near the other model config reads (around line 405):

**BEFORE:**
```python
    temperature    = config.get("model", {}).get("temperature", 0.2)
    max_tokens     = config.get("model", {}).get("max_tokens", 2048)
```

**AFTER:**
```python
    temperature    = config.get("model", {}).get("temperature", 0.2)
    max_tokens     = config.get("model", {}).get("max_tokens", 2048)
    repeat_penalty = config.get("model", {}).get("repeat_penalty", 1.0)
    repeat_last_n  = config.get("model", {}).get("repeat_last_n", 64)
```

**Why:** Reads the new fields from the merged config with the same neutral
defaults as the function signature. No behavior change for experiments
that don't set them.

---

## 5. experiment_runner.py — print bailed status clearly

In both loops, after the generate() call, the status line is printed:

**BEFORE:**
```python
                    print(f"  Status  : {result['status']}")
```

**AFTER:**
```python
                    if result["status"] == "bailed":
                        print(f"  Status  : {result['status']} "
                              f"⚠️  model emitted 0 tokens — silent bail")
                    else:
                        print(f"  Status  : {result['status']}")
```

**Why:** Makes the bailed condition immediately visible in the terminal
output rather than requiring log inspection to notice it.

---

## Expected outcome

After applying:
- e2b loop results should hit the 800-token ceiling much faster and terminate
- e2b silent bail results will show `status: bailed` in the run log
- Both failure modes are now distinguishable from successful runs
- The before/after comparison (with and without penalty) is the experiment

## Commit message

```
feat: repeat penalty config + eval_count capture for loop/bail detection
```
