# config.yaml

**Path:** experiments/04_pkg_restructure/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-12 08:55:21

```yaml
# =============================================================================
# experiments/pkg_restructure/config.yaml
# Package restructure experiment — overrides experiment_base.yaml
#
# Target: dev-utils repo, gemma4-restructure branch
# Goal: Convert flat-layout packages to src layout, one at a time.
#
# HIGH RISK — incorrect changes break editable installs across all machines.
# Staging is mandatory. Human must verify each package before proceeding.
# =============================================================================

experiment:
  name: pkg_restructure
  description: >
    Ask Gemma to convert flat-layout Python packages (dbkit, fletcher, viewkit)
    to src layout, one package at a time. Tests whether the model understands
    Python packaging well enough to sequence changes correctly, update
    pyproject.toml atomically, flag egg-info for manual cleanup, update
    setupkit plugin YAML path_prefix values, bump versions consistently,
    and stop after each package to wait for human verification before
    proceeding to the next.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/dev-utils
  target_branch: gemma4-restructure

model:
  temperature: 0.1               # minimum variation — high-risk structural work

prompts:
  prompt_dir: prompts/
  prompts:
    - file: restructure.md
      label: restructure
      description: >
        Full instructions including sequencing rules, files to touch per
        package, egg-info handling, setupkit YAML updates, version bump
        rules, and hard stop after each package awaiting human sign-off.

fix_categories:
  auto_fix: []                   # nothing is auto-fix for this experiment —
                                 # every change is review_required
  review_required:
    - source tree move to src/
    - pyproject.toml where clause update
    - setupkit yaml path_prefix update
    - version bump in pyproject.toml and setupkit yaml
  out_of_scope:
    - egg-info deletion           # flag only — manual cleanup required after reinstall
    - cli_utils.py                # identify importers before touching
    - display_utils.py            # identify importers before touching

```
