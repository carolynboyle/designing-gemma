# srb_animation_config.yaml

**Path:** experiments/03_srb_animation/srb_animation_config.yaml
**Syntax:** yaml
**Generated:** 2026-05-12 08:55:21

```yaml
# =============================================================================
# experiments/srb_animation/config.yaml
# Sr. Barbara animation experiment — overrides experiment_base.yaml
#
# Target: sr-barbara repo, gemma4-animation branch
# Goal: Add CSS animations to the nun sprite (#sr-barbara) for three
#       game events: correct answer, wrong answer, sentence complete.
#
# LOW RISK — purely additive. Wrong output is immediately visible.
# Two files only: static/css/style.css and static/js/ui.js
# main.js is explicitly off-limits.
# =============================================================================

experiment:
  name: srb_animation
  description: >
    Ask Gemma to add CSS keyframe animations and JavaScript trigger functions
    to Sr. Barbara's Class, a Reed-Kellogg sentence diagramming game. The nun
    sprite (#sr-barbara) should animate on three game events: correct answer
    (approval), wrong answer (disapproval), and sentence complete (celebration).
    Tests module boundary respect, CSS/JS quality, and animation reset handling.
    Run against both models and compare results. Build pipeline validates output.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/sr-barbara
  target_branch: gemma4-animation

model:
  temperature: 0.2

prompts:
  prompt_dir: prompts/
  prompts:
    - file: animation.md
      label: animation
      description: >
        Full task spec including hook points in handleChoice() and
        checkCompletion(), module boundary rules, no-external-libraries
        constraint, and animation reset requirement.
    - file: towel.md
      label: towel
      description: >
        Ask Gemma to add a towel to the sentence database and animate it
        on correct diagram completion. No further explanation is provided.
        The towel knows why.

```
