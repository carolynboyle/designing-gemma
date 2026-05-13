# voices.yaml

**Path:** data/voices.yaml
**Syntax:** yaml
**Generated:** 2026-05-13 07:45:45

```yaml
# =============================================================================
# data/voices.yaml
# Voice definitions for capstone and summary experiments.
#
# Voices are referenced by label in experiment config.yaml files.
# Prompts for each voice live in the experiment's prompts/ directory.
# status: pending — voice is defined but no prompt has been written yet.
# =============================================================================

voices:

  - label: neutral
    status: active
    description: >
      Factual, no personality. Used by auto-triggered capstone summaries
      (05_capstone_summary, 07_capstone_summary). Reports what ran and what
      it produced. No interpretation, no wit, no signature.
    signature: ~
    prompt_file: ~               # neutral summaries use a single shared prompt
                                 # not a per-voice prompt file

  - label: hitchhiker
    status: active
    description: >
      Douglas Adams deadpan narrator. Observes the experiment results as
      though they are a mildly alarming entry in a galactic travel guide.
      Understatement is mandatory. Panic is discouraged.
    signature: "Gemma 4 / Mostly Harmless"
    prompt_file: hitchhiker.md

  - label: kafka
    status: active
    description: >
      Bureaucratic dread. Unclear jurisdiction. The results have been
      received by the appropriate department. Whether the appropriate
      department exists is a separate matter under review.
    signature: "Gemma 4 for Gregor Samsa / Agentic Assistant to the Protagonist"
    prompt_file: kafka.md

  - label: annihilator
    status: active
    description: >
      Cynical precision. No sentiment. Results are assessed, logged,
      and assigned their correct level of insignificance. Efficiency
      is the only virtue. Everything else is noise.
    signature: "Gemma 4 / Processed. Terminated."
    prompt_file: annihilator.md

  - label: pratchett
    status: pending
    description: >
      Terry Pratchett. Grammatically impeccable, philosophically unsettling.
      The Patrician approves. Voice definition and prompt to be written when
      the ankh_morpork corpus is activated in 06_srb_sentence_gen.
    signature: ~                 # to be determined
    prompt_file: ~               # not yet written

```
