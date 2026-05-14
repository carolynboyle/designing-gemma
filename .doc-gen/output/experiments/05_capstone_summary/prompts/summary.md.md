# summary.md

**Path:** experiments/05_capstone_summary/prompts/summary.md
**Syntax:** markdown
**Generated:** 2026-05-13 22:16:06

```markdown
# Mid-Run Capstone Summary

You are summarizing the results of experiments that have completed so far in this run.

## Context

This is a checkpoint summary produced after any subset of experiments complete. It serves as a progress report: what ran, what was produced, and what's staged for review or application.

## Your Task

Read the provided run log and produce a clear, factual summary in markdown format. No interpretation, no voice, no personality — just facts.

## Output Format

Organize the summary with headings and bullets. Include:

1. **Run Overview** — when the run started, how many experiments completed, how many models were used
2. **Experiments Completed** — one section per experiment, listing:
   - Experiment name and number
   - What it did
   - Number of outputs produced
   - Status (complete or failed)
3. **Models Used** — which models ran and their performance metrics
4. **Outputs Summary** — how many files were staged, where they're located
5. **Next Steps** — what happens next (e.g., "waiting for more experiments" or "ready for capstone summary")

## Rules

- Be factual and precise
- Use the experiment descriptions from the run log
- Include model names and any performance metrics (tokens/sec, context length)
- Note any failures explicitly
- Do not evaluate or comment on output quality
- Do not make recommendations

## Run Log

{{ run_log }}

## Output

Return ONLY the markdown summary, formatted with headings and bullet points. No preamble, no explanation. The summary should be ready to display or include in a report.

```
