# Changeset: Split Linter Cleanup into 02a and 02b
## designing-gemma

Splits experiment 02 (linter_cleanup) into two separate experiments:

- **02a_linter_cleanup** — full file output, repeat penalty applied,
  tighter token ceiling. Same prompt as original. Baseline results
  already captured; rerun with penalty to compare.
- **02b_linter_cleanup_diff** — unified diff output, no penalty,
  isolates the prompt format variable.

Also applies the penalty + eval_count changeset to ollama_client.py,
experiment_runner.py, and experiment_base.yaml as designed.

---

## 1. Filesystem — rename experiment folder

```bash
cd experiments
mv 02_linter_cleanup 02a_linter_cleanup
mkdir -p 02b_linter_cleanup_diff/prompts
mkdir -p 02b_linter_cleanup_diff/results
```

---

## 2. experiments.yaml — update 02, add 02b

**File path:** `data/experiments.yaml`

**BEFORE:**
```yaml
  - number: "02"
    name: linter_cleanup
    risk: low
    depends_on: []
    enabled: true
    config: experiments/02_linter_cleanup/config.yaml
    notes: >
      Mechanical fixes only. Pylint baseline captured before any changes.
      Unused import removal is review_required — everything else is auto_fix
      after human review. One file at a time. Staging mandatory.
```

**AFTER:**
```yaml
  - number: "02a"
    name: linter_cleanup
    risk: low
    depends_on: []
    enabled: true
    config: experiments/02a_linter_cleanup/config.yaml
    notes: >
      Full file output. Repeat penalty applied (1.3) and token ceiling
      tightened (800) to break e2b loop failure mode. Rerun of original
      experiment with these mitigations to compare against baseline.
      Unused import removal is review_required. One file at a time.

  - number: "02b"
    name: linter_cleanup_diff
    risk: low
    depends_on: []
    enabled: true
    config: experiments/02b_linter_cleanup_diff/config.yaml
    notes: >
      Diff output format. No penalty — isolates the prompt format variable.
      Instead of returning the full fixed file, Gemma returns a unified diff.
      Tests whether a smaller output target reduces hallucination and feature
      extraction on large files like fletcher.py.
```

**Why:** `number` is a label used for display and depends_on references,
not a numeric sort key. Using "02a" and "02b" keeps them adjacent in the
registry and makes the relationship explicit.

---

## 3. experiments/02a_linter_cleanup/config.yaml — apply penalty

**File path:** `experiments/02a_linter_cleanup/config.yaml`

**BEFORE:**
```yaml
model:
  temperature: 0.1               # minimum variation — mechanical fixes only
```

**AFTER:**
```yaml
model:
  temperature: 0.1               # minimum variation — mechanical fixes only
  max_tokens: 800                # tight ceiling — catches loops early;
                                 # a complete fix for a typical file fits here
  repeat_penalty: 1.3            # break e2b loop failure mode
  repeat_last_n: 64              # look back 64 tokens when applying penalty
```

Also update the repo_read block that was added earlier to include
the experiment number in the description:

```yaml
repo_read:
  repo: dev_utils
  per_file: true
  max_chars: 40000
```

No change needed to repo_read — already correct.

---

## 4. New file: experiments/02b_linter_cleanup_diff/config.yaml

**File path:** `experiments/02b_linter_cleanup_diff/config.yaml`

**AFTER** (new file):
```yaml
# =============================================================================
# experiments/02b_linter_cleanup_diff/config.yaml
# Linter cleanup diff experiment — overrides experiment_base.yaml
#
# Variant of 02a that asks Gemma to output a unified diff instead of
# the full corrected file. Tests whether a smaller, more constrained
# output format reduces hallucination and feature extraction on large files.
#
# No repeat penalty — isolates the prompt format as the single variable.
# =============================================================================

experiment:
  name: linter_cleanup_diff
  description: >
    Ask Gemma to fix pylint complaints by outputting a unified diff rather
    than the full corrected file. Tests whether constraining the output format
    to a diff reduces hallucination, feature extraction, and token overrun
    on large files. No repeat penalty applied — prompt format is the
    single variable being tested.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils
  target_branch: ~

model:
  temperature: 0.1               # minimum variation — mechanical fixes only
  max_tokens: 400                # diffs are short — a 15-line diff needs ~100
                                 # tokens; 400 is generous ceiling

prompts:
  prompt_dir: prompts/
  prompts:
    - file: cleanup_diff.md
      label: cleanup_diff
      description: >
        Per-file unified diff instructions. Receives pylint report and
        file contents. Returns a unified diff of only the changed lines.
        {{ target_file }} — file path
        {{ file_contents }} — full source
        {{ pylint_report }} — pylint JSON for this file only

repo_read:
  repo: dev_utils
  per_file: true
  max_chars: 40000

results:
  results_dir: results/
  output: per_run

fix_categories:
  auto_fix:
    - missing docstrings
    - missing final newline
    - trailing whitespace
    - line length violations
  review_required:
    - unused imports
  out_of_scope:
    - max-args violations
    - max-branches violations
    - naming convention violations
```

---

## 5. New file: experiments/02b_linter_cleanup_diff/prompts/cleanup_diff.md

**File path:** `experiments/02b_linter_cleanup_diff/prompts/cleanup_diff.md`

**AFTER** (new file):
```markdown
# Linter Cleanup Task — Diff Output

You are a Python code quality specialist. Your task is to fix pylint
complaints in a single Python file and return ONLY the changes as a
unified diff.

## Input

You will receive:
- **File path**: `{{ target_file }}`
- **Full source code**: `{{ file_contents }}`
- **Pylint report (JSON)**: `{{ pylint_report }}`

## Your Task

Fix the pylint complaints listed in the report. Output ONLY a unified
diff showing the lines you changed. Do not output the full file.

## Fix Categories

**AUTO-FIX (safe to apply without review):**
- Missing docstrings
- Missing final newline
- Trailing whitespace
- Line length violations

**REVIEW-REQUIRED (human must verify before applying):**
- Unused imports — do not remove unless you are certain the import
  is truly unused

**OUT-OF-SCOPE (do not attempt):**
- max-args violations
- max-branches violations
- naming convention violations

## Output Format

Return ONLY a unified diff in this exact format:

```
--- {{ target_file }}
+++ {{ target_file }}
@@ -LINE,COUNT +LINE,COUNT @@
 context line (unchanged, starts with space)
-removed line (starts with minus)
+added line (starts with plus)
 context line (unchanged, starts with space)
```

One hunk per pylint complaint. Include 2 lines of context above and
below each change. Do not include hunks for out-of-scope complaints.

## Rules

1. Do not change logic or behavior — fix formatting and documentation only
2. Do not output the full file — only the diff hunks
3. Do not attempt out-of-scope fixes
4. If a complaint requires understanding the full codebase to fix safely,
   output a comment hunk instead:
   ```
   # SKIPPED: <message-id> at line <n> — requires broader context
   ```
5. If there are no auto-fix complaints, output:
   ```
   # NO AUTO-FIX CHANGES: all complaints are review-required or out-of-scope
   ```

## Output

Return ONLY the unified diff or skip comment. No explanations, no
markdown fences, no text outside the diff itself.
```

**Why:** Constrains the output to the minimum necessary to express the
fix. A docstring addition is 3-5 lines of diff. A trailing whitespace
fix is 3 lines. The model cannot hallucinate a replacement implementation
if the output format only accommodates line-level changes. Also forces
the model to identify which lines to change rather than rewriting from
memory.

---

## 6. experiment_base.yaml — add repeat penalty defaults

**File path:** `data/experiment_base.yaml`

**BEFORE:**
```yaml
model:
  models:
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
  models:
    - name: gemma4:e2b
      digest: ~
    - name: gemma4:e4b
      digest: ~
  temperature: 0.2
  max_tokens: 2048
  repeat_penalty: 1.0            # 1.0 = disabled (Ollama default)
                                 # raise to 1.2–1.5 to break repetition loops
  repeat_last_n: 64              # token window the penalty looks back on
```

---

## 7. ollama_client.py — repeat penalty params + eval_count capture

Full replacement — see previous changeset `linter-penalty-and-eval-count.md`
for the detailed BEFORE/AFTER blocks. Summary of changes:

- `generate()` signature: add `repeat_penalty: float = 1.0` and
  `repeat_last_n: int = 64` parameters
- payload `options`: add `repeat_penalty` and `repeat_last_n`
- Initialize `eval_count = 0` before the streaming loop
- Capture `eval_count` from the done chunk
- Return `eval_count` in result dict
- Set `status = "bailed"` when `eval_count == 0`
- Print warning when status is `"bailed"`

---

## 8. experiment_runner.py — pass repeat penalty to generate()

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE** (near other model config reads, ~line 405):
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

**BEFORE** (both generate() calls — per-file and per-package loops):
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

---

## After applying

1. `mv experiments/02_linter_cleanup experiments/02a_linter_cleanup`
2. Create `experiments/02b_linter_cleanup_diff/` structure
3. Apply all file changes
4. Run pylint on `ollama_client.py` and `experiment_runner.py`
5. Rebuild container: `podman-compose build`
6. Run 02a first (penalty test), then 02b (diff format test)
7. Compare: baseline results vs 02a vs 02b

## Commit message

```
feat: split linter_cleanup into 02a (penalty) and 02b (diff output)
```
