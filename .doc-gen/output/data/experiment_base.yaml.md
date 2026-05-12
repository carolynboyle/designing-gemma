# experiment_base.yaml

**Path:** data/experiment_base.yaml
**Syntax:** yaml
**Generated:** 2026-05-12 08:55:21

```yaml
# =============================================================================
# experiment_base.yaml
# Base configuration inherited by all experiments.
# Override any field in the experiment's own config.yaml.
#
# Loading rule: base values apply unless the experiment config specifies
# an override. Experiment config wins on all conflicts.
# =============================================================================

experiment:
  name: ~                        # required — override in experiment config
  description: ~                 # required — override in experiment config
  experiment_version: 1          # increment when prompt or scope changes meaningfully
  target_repo: ~                 # required — path or URL of repo under test
  target_branch: ~               # optional — null means use current branch

model:
  models:                        # run experiment against each model in list
    - name: gemma4:e2b
      digest: ~                  # pin after first run: ollama show gemma4:e2b --verbose
    - name: gemma4:e4b
      digest: ~                  # pin after first run: ollama show gemma4:e4b --verbose
  temperature: 0.2               # low = deterministic; raise for capstone/voice tasks
  max_tokens: 2048

prompts:
  prompt_dir: prompts/
  prompts: []                    # list of prompt files — override in experiment config
  # Prompt files use Jinja2 template syntax for injecting file contents.
  # Available variables depend on experiment — defined in experiment config.
  # Example: {{ input_code }}, {{ target_file }}, {{ pylint_report }}

results:
  results_dir: results/
  output: per_run                # per_run | combined
  staging: true                  # always stage output; never write directly to target repo
                                 # this field may not be overridden to false

# =============================================================================
# run_log
# Schema for entries written to run_log.yaml after each Gemma interaction.
# The Python script writes these automatically. Do not edit manually.
# Fields marked "auto" are captured by ollama_client.py at runtime.
# =============================================================================

run_log:
  log_file: run_log.yaml
  # Per-run entry schema:
  #   id:                  run_001, run_002 ... (auto)
  #   timestamp:           ISO 8601 (auto)
  #   experiment:          experiment name (auto)
  #   experiment_version:  from config (auto)
  #   model:               model name (auto)
  #   model_digest:        pinned digest hash (auto)
  #   prompt_file:         path to prompt file (auto)
  #   output_file:         path to staged result (auto)
  #   tokens_per_second:   inference rate (auto)
  #   context_length:      total tokens in context (auto)
  #   status:              pending | complete | failed (auto)
  #   documented:          [{capstone_id, voice, output_file}] (human-updated)
  #   tags:                [] (human-updated)
  #   notes:               ~ (human-updated)
  documented: []

# =============================================================================
# fix_categories
# Only meaningful for linter_cleanup and pkg_restructure. Present but inert
# for all other experiments. Override in relevant experiment config.yaml.
# =============================================================================

fix_categories:
  auto_fix: []                   # safe to stage and apply after human review
  review_required: []            # human must approve each individual change
  out_of_scope: []               # document in run log but do not attempt to fix

```
