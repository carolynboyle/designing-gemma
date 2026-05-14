# experiments.yaml

**Path:** data/experiments.yaml
**Syntax:** yaml
**Generated:** 2026-05-14 07:38:25

```yaml
# =============================================================================
# data/experiments.yaml
# Master experiment registry for designing-gemma.
#
# This file is the authoritative list of all experiments in run order.
# It is a registry only — operational details live in each experiment's
# own config.yaml. The runner reads this file to know what exists and
# what order to run it in. Experiment configs tell it what to do.
#
# Fields:
#   number:      two-digit run order prefix matching the folder name
#   name:        must match experiment.name in the experiment's config.yaml
#   risk:        none | low | medium | high
#   depends_on:  list of experiment numbers that should complete first.
#                [] means no dependencies — can run in any order.
#   enabled:     true | false — false disables without removing from registry
#   config:      path to the experiment's config.yaml
#   notes:       human-readable context for the registry entry
# =============================================================================

experiments:

  - number: "01"
    name: readme_gen
    risk: none
    depends_on: []
    enabled: true
    config: experiments/01_readme_gen/config.yaml
    notes: >
      Read-only. Gemma reads existing package structure and generates or
      standardizes README files for every tool in dev-utils. No code changes.
      Safe to run first or at any time.

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

  - number: "03"
    name: srb_animation
    risk: medium
    depends_on: []
    enabled: true
    config: experiments/03_srb_animation/config.yaml
    notes: >
      Additive JS and CSS only. Targets sr-barbara repo on gemma4-animation
      branch. main.js is explicitly off-limits. Wrong output is immediately
      visible in the browser. The towel prompt is exactly what it sounds like.

  - number: "04"
    name: pkg_restructure
    risk: high
    depends_on: []
    enabled: true
    config: experiments/04_pkg_restructure/config.yaml
    notes: >
      Converts flat-layout Python packages to src layout. Targets dev-utils
      repo on gemma4-restructure branch. Incorrect changes break editable
      installs across all machines. Run last among code tasks. Hard stop
      after each package — human must verify before proceeding.

  - number: "05"
    name: capstone_summary
    risk: none
    depends_on: []
    enabled: false
    config: experiments/05_capstone_summary/config.yaml
    notes: >
      Disabled for this run — running all experiments straight through to 07.
      This experiment exists for multi-day or partial runs where a mid-run
      checkpoint summary is useful. Enable it, run it after any subset of
      experiments, and it will produce a factual neutral-voice summary of
      whatever has completed so far. No voice, no interpretation — just
      what ran and what it produced. Re-enable for future runs where you
      want a progress snapshot before continuing.

  - number: "06"
    name: srb_sentence_gen
    risk: none
    depends_on: []
    enabled: true
    config: experiments/06_srb_sentence_gen/config.yaml
    notes: >
      Generative only — output is staged SQL reviewed and selectively applied
      by a human via Adminer. Nothing touches the database automatically.
      Three corpora (hitchhiker, metamorphosis, terminator). ankh_morpork
      corpus is defined but pending — Pratchett voice not yet written.
      Human must query Adminer for ID offsets before each run.

  - number: "07"
    name: capstone_summary
    risk: none
    depends_on: ["01", "02", "03", "04", "06"]
    enabled: true
    config: experiments/07_capstone_summary/config.yaml
    notes: >
      Auto-triggered after all generative experiments complete. Neutral voice.
      Factual summary of the full run — what ran, what each model produced,
      what was staged, what was applied. No interpretation. Feeds into 08.

  - number: "08"
    name: capstone_readme
    risk: none
    depends_on: ["01", "02", "03", "04", "06", "07"]
    enabled: true
    config: experiments/08_capstone_readme/config.yaml
    notes: >
      Human-initiated. Runs last. Gemma writes the README in one of three
      voices (hitchhiker, kafka, annihilator) and signs it. This is the
      artifact the Dev.to article is built around. The towel is mentioned.

```
