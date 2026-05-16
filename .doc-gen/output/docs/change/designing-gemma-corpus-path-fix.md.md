# designing-gemma-corpus-path-fix.md

**Path:** docs/change/designing-gemma-corpus-path-fix.md
**Syntax:** markdown
**Generated:** 2026-05-15 14:53:19

```markdown
# Changeset: Corpus Path Resolution Fix
## designing-gemma

Fixes corpus file loading for experiments that specify `source_type: file`.
Relative paths in corpus config were being resolved from the working directory
rather than the experiment directory, causing FileNotFoundError at runtime.

---

## 1. src/designing_gemma/experiment_runner.py

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE:**
```python
            # Build Jinja2 context — start from base, add corpus if present
            context = dict(base_context)
            if corpus:
                try:
                    corpus_text = load_corpus(
                        corpus["source"], corpus["source_type"]
                    )
                    context["source_text"] = corpus_text
                except PromptError as e:
                    print(f"  ERROR loading corpus {corpus_label}: {e}")
                    continue
```

**AFTER:**
```python
            # Build Jinja2 context — start from base, add corpus if present
            context = dict(base_context)
            if corpus:
                try:
                    source = corpus["source"]
                    if corpus["source_type"] == "file":
                        source = str(experiment_dir / source)
                    corpus_text = load_corpus(source, corpus["source_type"])
                    context["source_text"] = corpus_text
                except PromptError as e:
                    print(f"  ERROR loading corpus {corpus_label}: {e}")
                    continue
```

**Why:** `experiment_dir` is already resolved earlier in `_run_experiment()`
as `Path(config_path).parent`. File-type corpus paths are relative to the
experiment directory (e.g. `corpora/hhg_excerpt.txt` lives under
`experiments/06_srb_sentence_gen/`). URL-type corpora are unaffected — the
`if` guard only resolves paths for `source_type: file`.

---

## After Applying

- Run `pytest` to verify nothing broke
- Populate `experiments/06_srb_sentence_gen/corpora/hhg_excerpt.txt` and
  `terminator_excerpt.txt` with content before running experiment 06
- The `ankh_morpork_excerpt.txt` corpus is `status: pending` and will not
  be loaded until activated in config

```
