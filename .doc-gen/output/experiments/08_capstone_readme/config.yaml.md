# config.yaml

**Path:** experiments/08_capstone_readme/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-13 07:45:45

```yaml
# =============================================================================
# experiments/08_capstone_readme/config.yaml
# Voiced capstone README — overrides experiment_base.yaml
#
# Human-initiated. Runs last, after 07_capstone_summary completes.
# Gemma writes the README in three voices and signs each one.
# All three voices run against both models — six README candidates total.
# Human selects the final README for the repo.
#
# The towel is mentioned.
# =============================================================================

experiment:
  name: capstone_readme
  description: >
    Ask Gemma to write the designing-gemma README in three distinct voices —
    hitchhiker, kafka, and annihilator — using the factual capstone summary
    from 07 as grounding. All three voices run against both models, producing
    six README candidates. Human selects one. Gemma signs it. Tests creative
    voice consistency, factual accuracy under persona, and the ability to
    write something a human would actually want to read.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/designing-gemma
  target_branch: ~               # output staged for human review — no branch needed

model:
  temperature: 0.7               # highest temperature in the suite — creative voice work
                                 # needs room to be interesting

prompts:
  prompt_dir: prompts/
  prompts:
    - file: hitchhiker.md
      label: hitchhiker
      description: >
        Douglas Adams deadpan narrator. The README is a mildly alarming entry
        in a galactic travel guide. Understatement mandatory. Panic discouraged.
        Gemma signs: "Gemma 4 / Mostly Harmless"

    - file: kafka.md
      label: kafka
      description: >
        Bureaucratic dread, unclear jurisdiction. Gregor Samsa woke one morning
        to find he had become a monstrous AI assistant. He was not entirely sure
        this was worse than before. The results have been filed. The appropriate
        department has been notified. Whether the appropriate department exists
        is a separate matter under review.
        Gemma signs: "Gemma 4 for Gregor Samsa / Agentic Assistant to the Protagonist"

    - file: annihilator.md
      label: annihilator
      description: >
        Cynical precision. No sentiment. Results assessed, logged, assigned
        their correct level of insignificance. Efficiency is the only virtue.
        Everything else is noise.
        Gemma signs: "Gemma 4 / Processed. Terminated."

# =============================================================================
# context
# The 07_capstone_summary output is injected as {{ capstone_summary }}.
# All three prompts receive the same factual grounding — voice is the
# only variable. Prompts must instruct Gemma to stay factually accurate
# while writing in persona.
# =============================================================================

context:
  capstone_summary: "{{ capstone_summary }}"   # injected from 07 results at runtime

results:
  results_dir: results/
  output: per_run                # one README candidate per model per voice = six total

```
