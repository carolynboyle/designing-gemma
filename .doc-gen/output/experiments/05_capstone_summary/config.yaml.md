# config.yaml

**Path:** experiments/05_capstone_summary/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-12 13:04:48

```yaml
# =============================================================================
# experiments/05_capstone_summary/config.yaml
# Mid-run capstone summary — overrides experiment_base.yaml
#
# DISABLED in experiments.yaml for this run — all experiments running
# straight through to 07_capstone_summary.
#
# Purpose: Auto-triggered checkpoint summary after any subset of experiments.
# Useful for multi-day or partial runs where you want a progress snapshot
# before continuing. Re-enable in experiments.yaml when needed.
#
# Voice: neutral — factual, no personality, no signature.
# =============================================================================

experiment:
  name: capstone_summary
  description: >
    Produce a factual neutral-voice summary of whichever experiments have
    completed so far. Reports what ran, what each model produced, what was
    staged, and what was applied. No interpretation, no voice, no signature.
    Intended as a mid-run checkpoint for multi-day or partial runs.
  experiment_version: 1
  target_repo: ~                 # generative only — no target repo
  target_branch: ~

model:
  temperature: 0.1               # minimum variation — factual reporting only

prompts:
  prompt_dir: prompts/
  prompts:
    - file: summary.md
      label: summary
      description: >
        Neutral factual summary prompt. Receives run_log.yaml contents via
        Jinja2 template variable {{ run_log }}. Reports completed experiments,
        models used, output files staged, and any failures or skipped runs.
        No voice. No interpretation.

results:
  results_dir: results/
  output: per_run

```
