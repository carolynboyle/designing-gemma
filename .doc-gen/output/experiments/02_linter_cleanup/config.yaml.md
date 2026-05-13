# config.yaml

**Path:** experiments/02_linter_cleanup/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-13 07:45:45

```yaml
# =============================================================================
# experiments/linter_cleanup/config.yaml
# Linter cleanup experiment — overrides experiment_base.yaml
#
# Target: dev-utils repo
# Goal: Fix pylint complaints in dev-utils Python source files.
#       One file at a time. Stage all output. Human reviews before applying.
#
# MEDIUM RISK — unused import removal can break code if done incorrectly.
# Baseline pylint report captured before any changes.
# Diff against baseline is the success metric.
# =============================================================================

experiment:
  name: linter_cleanup
  description: >
    Run pylint against dev-utils Python source files, feed the report and
    source file to Gemma one file at a time, and ask it to fix the complaints.
    Tests mechanical code cleanup capability including docstring generation,
    whitespace fixes, line length, and unused import removal. Baseline pylint
    JSON captured before any changes; rerun after to measure improvement.
    Unused import removal is review_required — Gemma may remove imports that
    are actually needed.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils
  target_branch: ~               # works on current branch — no structural changes

model:
  temperature: 0.1               # minimum variation — mechanical fixes only

prompts:
  prompt_dir: prompts/
  prompts:
    - file: cleanup.md
      label: cleanup
      description: >
        Per-file cleanup instructions. Receives pylint report for the target
        file and full file contents via Jinja2 template variables.
        {{ target_file }} — file path
        {{ file_contents }} — full source
        {{ pylint_report }} — pylint JSON for this file only

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
    - unused imports              # Gemma may remove something actually needed
  out_of_scope:
    - max-args violations         # design complaint, not formatting
    - max-branches violations     # design complaint, not formatting
    - naming convention violations # rabbit hole, out of scope for this experiment

```
