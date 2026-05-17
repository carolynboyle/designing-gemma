# Changeset: template_vars Config Injection
## designing-gemma

Adds support for arbitrary template variables defined in experiment
config and injected into the Jinja2 render context. Motivated by
experiment 05 (srb_sentence_gen) guided prompt, which requires
`{{ sentence_id_base }}` and `{{ part_id_base }}` — ID offset values
that prevent INSERT collisions with existing database rows.

Convention: sentence_id_base increments by 1000 per run (1000, 2000,
3000...) so each run's rows are grouped together with obvious gaps
between batches. Easy to identify, easy to roll back.

---

## 1. experiment_runner.py — merge template_vars into Jinja2 context

**File path:** `src/designing_gemma/experiment_runner.py`

**BEFORE** (line ~703, inside the corpus loop):
```python
                # Build Jinja2 context — start from base, add corpus if present
                context = dict(base_context)
                if package_name:
                    context["package_name"] = package_name
                if corpus:
```

**AFTER:**
```python
                # Build Jinja2 context — start from base, add corpus if present
                context = dict(base_context)

                # Inject template_vars from config (e.g. sentence_id_base)
                template_vars = config.get("template_vars", {})
                if template_vars:
                    context.update(template_vars)

                if package_name:
                    context["package_name"] = package_name
                if corpus:
```

**Why:** Generic injection point — any experiment can define
`template_vars` in its config and those values become available in
prompt templates. Experiments that don't define it are unaffected.
Placed before corpus loading so corpus values can override if needed.

---

## 2. experiments/05_srb_sentence_gen/config.yaml — add template_vars

**File path:** `experiments/05_srb_sentence_gen/config.yaml`

Add the following block before the `results:` section:

**BEFORE:**
```yaml
results:
  results_dir: results/
  output: per_run
```

**AFTER:**
```yaml
# =============================================================================
# template_vars
# Injected into Jinja2 prompt context before rendering.
# sentence_id_base and part_id_base prevent INSERT collisions with
# existing rows. Increment both by 1000 before each new run batch.
#
# Run history:
#   Run 1 (2026-05-16): base 1000
# =============================================================================

template_vars:
  sentence_id_base: 1000
  part_id_base: 1000

results:
  results_dir: results/
  output: per_run
```

**Why:** Provides the values the guided prompt needs to render.
The run history comment documents what base was used for each batch
so the correct next value is never a guess.

---

## After applying

1. Apply the one-line change to `experiment_runner.py`
2. Add `template_vars` block to `config.yaml`
3. Rebuild container: `podman-compose build`
4. Run experiment 05 guided prompts only — verify prompt renders
   and SQL uses id offsets starting at 1000
5. Before next run batch: increment both values to 2000

## Commit message

```
feat: add template_vars config injection — fixes guided prompt sentence_id_base
```
