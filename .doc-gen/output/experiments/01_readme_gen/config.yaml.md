# config.yaml

**Path:** experiments/01_readme_gen/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-15 14:53:19

```yaml
# =============================================================================
# experiments/readme_gen/config.yaml
# README generation experiment — overrides experiment_base.yaml
#
# Target: dev-utils repo
# Goal: Generate or standardize README files for every tool in the repo.
#
# Two prompt passes:
#   unguided — no structural hints; test what Gemma infers independently
#   guided   — explicit package definitions and required sections provided
#
# Style standard: python/fletcher/README.md in the target repo.
# =============================================================================

experiment:
  name: readme_gen
  description: >
    Ask Gemma to read existing package structure and generate or standardize
    README files for every tool in the dev-utils repo. Run twice: once with
    no structural guidance (unguided), once with explicit package definitions
    (guided). Compare results between passes and between models.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils

model:
  temperature: 0.3               # slight bump over base — README prose benefits
                                 # from a little more variation than pure code tasks

prompts:
  prompt_dir: prompts/
  prompts:
    - file: unguided.md
      label: unguided
      description: >
        No structural hints provided. Tests whether Gemma can independently
        distinguish packages from subdirectories and infer what needs a README.
    - file: guided.md
      label: guided
      description: >
        Explicit package definitions, required README sections, and style
        standard provided. Tests instruction-following and output quality
        when given a complete spec.

repo_read:
  per_package: true
  repo: dev_utils
  manifest: .doc-gen/manifest.python.yml
  manifest_filter:
    source: .doc-gen/manifest.yml
    include:
      - python/
  max_chars: 80000
  size_overrides:
    - python/fletcher/README.md

    
```
