# project-structure.md

**Path:** docs/project-structure.md
**Syntax:** markdown
**Generated:** 2026-05-12 08:55:21

```markdown
# designing-gemma: Canonical Project Structure

Last updated: 2026-05-09

This document is the authoritative reference for the project directory structure.
Update it when the structure changes. Do not let it drift from the actual repo.

---

> **Correction:** Experiment numbering revised from original plan:
> 01_readme_gen, 02_linter_cleanup, 03_srb_animation, 04_pkg_restructure,
> 05_capstone_summary (runs after any subset), 06_srb_sentence_gen,
> 07_capstone_readme (was 08; 07 is now freed up)

---

## Full Directory Tree

```
designing-gemma/
├── src/
│   └── designing_gemma/
│       ├── __init__.py
│       ├── ollama_client.py       # Ollama API client — all model calls go here
│       ├── config.py              # Config loader — merges base + experiment config
│       ├── prompt_loader.py       # Jinja2 prompt templating — injects file contents
│       └── experiment_runner.py  # Orchestrates a single experiment run end-to-end
├── experiments/
│   ├── 01_readme_gen/             # LOWEST RISK — read only, no code changes
│   │   ├── prompts/
│   │   │   ├── unguided.md        # No structural hints — tests Gemma's inference
│   │   │   └── guided.md          # Full spec provided — tests instruction following
│   │   ├── config.yaml
│   │   └── results/               # Staged output + run_log.yaml land here
│   ├── 02_linter_cleanup/         # LOW RISK — mechanical fixes, staging required
│   │   ├── prompts/
│   │   │   └── cleanup.md         # Per-file cleanup — uses Jinja2 template variables
│   │   ├── config.yaml
│   │   └── results/
│   ├── 03_srb_animation/          # MEDIUM RISK — additive JS/CSS, separate repo
│   │   ├── prompts/
│   │   │   ├── animation.md       # Nun sprite animation for three game events
│   │   │   └── towel.md           # The towel. The towel knows why.
│   │   ├── config.yaml
│   │   └── results/
│   ├── 04_pkg_restructure/        # HIGH RISK — breaks editable installs if wrong
│   │   ├── prompts/
│   │   │   └── restructure.md     # Flat → src layout, one package at a time
│   │   ├── config.yaml
│   │   └── results/
│   ├── 05_capstone_summary/       # Auto-triggered after runs — factual, no voice
│   │   ├── prompts/
│   │   │   └── summary.md         # Neutral summary of what ran and what it produced
│   │   ├── config.yaml
│   │   └── results/
│   ├── 06_srb_sentence_gen/       # NONE — staged SQL only, human applies via Adminer
│   │   ├── prompts/
│   │   │   ├── unguided.md        # Schema inferred from worked examples only
│   │   │   └── guided.md          # Full schema spec + constraints provided
│   │   ├── corpora/
│   │   │   ├── hhg_excerpt.txt    # Hitchhiker's Guide — file, not public domain
│   │   │   ├── terminator_excerpt.txt  # Terminator screenplay — file, short excerpt
│   │   │   └── ankh_morpork_excerpt.txt  # Future — pending Pratchett voice
│   │   ├── config.yaml
│   │   └── results/               # Staged SQL blocks — never auto-applied
│   ├── 07_capstone_summary/       # Auto-triggered after all experiments — factual
│   │   ├── prompts/
│   │   │   └── summary.md
│   │   ├── config.yaml
│   │   └── results/
│   └── 08_capstone_readme/        # Human-initiated — voiced, runs last
│       ├── prompts/
│       │   ├── hitchhiker.md      # Douglas Adams narrator — signs: "Mostly Harmless"
│       │   ├── kafka.md           # Bureaucratic dread — signs: "For Gregor Samsa"
│       │   └── annihilator.md     # Cynical precision — signs: "Processed. Terminated."
│       ├── config.yaml
│       └── results/
├── scripts/                       # Standalone utility scripts — no experiment logic
├── data/
│   ├── experiment_base.yaml       # Base config inherited by all experiments
│   ├── experiments.yaml           # Master experiment registry
│   └── voices.yaml                # Voice definitions for capstone and summary
├── pyproject.toml                 # Single source of truth for package version
└── README.md                      # Written by Gemma. Signed. The towel is mentioned.
```

---

## Experiment Numbering

Folders are prefixed with a two-digit number indicating the recommended run order.
Lower numbers are safer. Higher numbers depend on lower ones being complete.

| # | Experiment | Risk | Depends On |
|---|------------|------|------------|
| 01 | readme_gen | None — read only | Nothing |
| 02 | linter_cleanup | Low — mechanical fixes | Nothing |
| 03 | srb_animation | Medium — separate repo | Nothing |
| 04 | pkg_restructure | High — breaks installs | Nothing, but run last among code tasks |
| 05 | capstone_summary | None — generative | Any completed experiments |
| 06 | srb_sentence_gen | None — staged SQL only | Nothing |
| 07 | capstone_summary | None — generative | All generative experiments complete |
| 08 | capstone_readme | None — generative | All experiments complete |

Numbering is assigned manually for now. Future Designing Gemma webapp will
assign prefixes automatically based on max(existing) + 1.

---

## Corpus Sources (06_srb_sentence_gen)

| Label | Voice | Source | Type | Status |
|-------|-------|--------|------|--------|
| hitchhiker | Hitchhiker | HHG excerpt | file | active |
| metamorphosis | Kafka | Project Gutenberg | url | active |
| terminator | Annihilator | Screenplay excerpt | file | active |
| ankh_morpork | Pratchett | TBD | file | pending |

---

## Results Layout

Every experiment's results/ folder contains a run_log.yaml and staged output files.
Output files are named: run_{id}_{model}_{prompt_label}_{corpus_label}.ext

---

## Key Design Decisions

Staging is mandatory. Output never goes directly to the target repo or database.

YAML is the source of truth. All experiment configuration lives in YAML files.

Jinja2 for prompt templating. Prompt .md files use variable syntax.

SQL is never auto-applied. Experiment 06 output is staged SQL only.

---

## Future: Designing Gemma Webapp (v2.0)

See Obsidian notes for full v2.0 feature spec.

```
