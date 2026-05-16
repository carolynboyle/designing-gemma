# designing-gemma-repo-context.md

**Path:** docs/change/designing-gemma-repo-context.md
**Syntax:** markdown
**Generated:** 2026-05-15 14:53:19

```markdown
# Changeset: Repo Path Context Injection
## designing-gemma

Adds a `repos` block to `experiment_base.yaml` containing container-side paths
for the two target repos. Updates `experiment_runner.py` to inject `repos` into
the Jinja2 prompt context for every run, so prompts can reference repo paths
via `{{ repos.dev_utils }}` and `{{ repos.sr_barbara }}` without hardcoding paths
in prompt text.

---

## 1. data/experiment_base.yaml

**File path:** `data/experiment_base.yaml`

**BEFORE:**
```yaml
experiment:
  name: ~                        # required — override in experiment config
  description: ~                 # required — override in experiment config
  experiment_version: 1          # increment when prompt or scope changes meaningfully
  target_repo: ~                 # required — path or URL of repo under test
  target_branch: ~               # optional — null means use current branch
```

**AFTER:**
```yaml
experiment:
  name: ~                        # required — override in experiment config
  description: ~                 # required — override in experiment config
  experiment_version: 1          # increment when prompt or scope changes meaningfully
  target_repo: ~                 # required — path or URL of repo under test
  target_branch: ~               # optional — null means use current branch

# =============================================================================
# repos
# Container-side paths to target repositories, mounted via docker-compose.
# These are injected into every prompt context as {{ repos.dev_utils }} etc.
# Paths are stable inside the container regardless of host OS.
# =============================================================================

repos:
  dev_utils: /repos/dev-utils
  sr_barbara: /repos/sr-barbara
```

**Why:** Repo paths belong in config, not in prompt text. The container paths
are consistent across host platforms because docker-compose mounts them at
these fixed locations. Individual experiments reference whichever repos they
need via Jinja2 template variables.

---

## 2. src/designing_gemma/experiment_runner.py

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE:**
```python
    for prompt_def in prompts:
        prompt_file  = prompt_def.get("file")
        prompt_label = prompt_def.get("label", prompt_file)

        for corpus in corpus_list:
            corpus_label = corpus["label"] if corpus else None

            # Build Jinja2 context
            context = {}
            if corpus:
                try:
                    corpus_text = load_corpus(
                        corpus["source"], corpus["source_type"]
                    )
                    context["source_text"] = corpus_text
                except PromptError as e:
                    print(f"  ERROR loading corpus {corpus_label}: {e}")
                    continue

            # Render prompt
            try:
                rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
            except PromptError as e:
                print(f"  ERROR rendering prompt {prompt_file}: {e}")
                continue
```

**AFTER:**
```python
    # Build base context — available to all prompts in this experiment
    repos = config.get("repos", {})
    base_context = {"repos": repos} if repos else {}

    for prompt_def in prompts:
        prompt_file  = prompt_def.get("file")
        prompt_label = prompt_def.get("label", prompt_file)

        for corpus in corpus_list:
            corpus_label = corpus["label"] if corpus else None

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

            # Render prompt
            try:
                rendered_prompt = load_prompt(prompt_file, prompt_dir, context)
            except PromptError as e:
                print(f"  ERROR rendering prompt {prompt_file}: {e}")
                continue
```

**Why:** Extracts `repos` from the merged config once before the prompt loop
and seeds every context dict with it. Uses `dict(base_context)` to avoid
mutating the base across iterations. The change is additive — experiments
without a `repos` block get an empty base context, same as before.

---

## After Applying

- Run `pytest` to verify nothing broke
- Prompts can now use `{{ repos.dev_utils }}` and `{{ repos.sr_barbara }}`
- Add additional repo entries to the `repos` block in `experiment_base.yaml`
  if future experiments target other repos

```
