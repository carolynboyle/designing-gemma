# summary.md

**Path:** experiments/07_capstone_summary/prompts/summary.md
**Syntax:** markdown
**Generated:** 2026-05-13 22:16:06

```markdown
# Full-Run Capstone Summary

You are summarizing the complete results of all experiments in this run.

## Context

This summary is produced after all experiments complete. It serves as the factual foundation for the voiced capstone README (which will be written by Gemma in one of three voices based on this summary). Your job is to provide the grounded facts — the voiced README will interpret them through a specific persona.

## Your Task

Read the provided run log and produce a clear, factual summary in markdown format. This will be injected into the voice prompts as context, so accuracy and clarity are critical. No interpretation, no voice, no personality — just facts.

## Output Format

Organize the summary with headings and bullets. Include:

1. **Run Overview** — when the run started, total duration, how many experiments completed, how many models were used
2. **Experiments Completed** — one section per experiment (in order), listing:
   - Experiment name and number
   - What it did
   - Number of outputs produced
   - Status (complete or failed)
3. **Models Used** — which models ran, their digests, and any performance metrics (tokens/sec, context length)
4. **Outputs Summary** — total files staged, organized by experiment and model
5. **Key Results** — notable metrics or outcomes (e.g., "Experiment 06 generated 40 SQL sentences across three corpora")
6. **Next Steps** — the voiced README will be generated from this summary

## Rules

- Be factual and precise — this is the source of truth for the voiced README
- Use experiment names and descriptions from the run log
- Include model names, digests, and performance metrics
- Note any failures explicitly
- Organize data clearly so a voice prompt can extract and interpret it effectively
- Do not evaluate or comment on output quality
- Do not make recommendations

## Run Log

{{ run_log }}

## Output

Return ONLY the markdown summary, formatted with headings and bullet points. No preamble, no explanation. This summary will be injected into voice prompts, so clarity and completeness are essential.

```
