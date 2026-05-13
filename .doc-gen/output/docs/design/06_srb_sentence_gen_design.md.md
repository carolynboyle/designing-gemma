# 06_srb_sentence_gen_design.md

**Path:** docs/design/06_srb_sentence_gen_design.md
**Syntax:** markdown
**Generated:** 2026-05-13 07:45:45

```markdown
# designing-gemma: Canonical Project Structure

Last updated: 2026-05-09

This document is the authoritative reference for the project directory structure.
Update it when the structure changes. Do not let it drift from the actual repo.

---

## Full Directory Tree

```
designing-gemma/
├── src/
│   └── gemma4_experiment/
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
│   │
│   ├── 02_linter_cleanup/         # LOW RISK — mechanical fixes, staging required
│   │   ├── prompts/
│   │   │   └── cleanup.md         # Per-file cleanup — uses Jinja2 template variables
│   │   ├── config.yaml
│   │   └── results/
│   │
│   ├── 03_srb_animation/          # MEDIUM RISK — additive JS/CSS, separate repo
│   │   ├── prompts/
│   │   │   ├── animation.md       # Nun sprite animation for three game events
│   │   │   └── towel.md           # The towel. The towel knows why.
│   │   ├── config.yaml
│   │   └── results/
│   │
│   ├── 04_pkg_restructure/        # HIGH RISK — breaks editable installs if wrong
│   │   ├── prompts/
│   │   │   └── restructure.md     # Flat → src layout, one package at a time
│   │   ├── config.yaml
│   │   └── results/
│   │
│   ├── 05_capstone_summary/       # Auto-triggered after runs — factual, no voice
│   │   ├── prompts/
│   │   │   └── summary.md         # Neutral summary of what ran and what it produced
│   │   ├── config.yaml
│   │   └── results/
│   │
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
│   │
│   ├── 07_capstone_summary/       # Auto-triggered after all experiments — factual
│   │   ├── prompts/
│   │   │   └── summary.md
│   │   ├── config.yaml
│   │   └── results/
│   │
│   └── 08_capstone_readme/        # Human-initiated — voiced, runs last
│       ├── prompts/
│       │   ├── hitchhiker.md      # Douglas Adams narrator — signs: "Mostly Harmless"
│       │   ├── kafka.md           # Bureaucratic dread — signs: "For Gregor Samsa"
│       │   └── annihilator.md     # Cynical precision — signs: "Processed. Terminated."
│       ├── config.yaml
│       └── results/
│
├── scripts/                       # Standalone utility scripts — no experiment logic
│
├── data/
│   ├── experiment_base.yaml       # Base config inherited by all experiments
│   ├── experiments.yaml           # Master experiment registry
│   └── voices.yaml                # Voice definitions for capstone and summary
│
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
assign prefixes automatically based on `max(existing) + 1`.

---

## Corpus Sources (06_srb_sentence_gen)

| Label | Voice | Source | Type | Status |
|-------|-------|--------|------|--------|
| hitchhiker | Hitchhiker | HHG excerpt — library/preview copy | file | active |
| metamorphosis | Kafka | Project Gutenberg — public domain | url | active |
| terminator | Annihilator | Screenplay excerpt — personal use | file | active |
| ankh_morpork | Pratchett | TBD | file | pending |

Metamorphosis URL: `https://www.gutenberg.org/files/5200/5200-0.txt`

---

## Results Layout

Every experiment's `results/` folder contains:

```
results/
├── run_log.yaml                   # Append-only log of every run
├── run_001_e2b_<label>.md         # Staged output — never written directly to target repo
├── run_002_e4b_<label>.md
└── ...
```

For 06_srb_sentence_gen, output files are staged SQL:
```
results/
├── run_log.yaml
├── run_001_e2b_unguided_hitchhiker.sql
├── run_002_e4b_unguided_hitchhiker.sql
└── ...
```

Output files are named: `run_{id}_{model}_{prompt_label}_{corpus_label}.sql`

---

## Key Design Decisions

**Staging is mandatory.** Output never goes directly to the target repo or
database. The Python script writes to `results/`, the human reviews, then
applies manually or with a separate apply script.

**YAML is the source of truth.** All experiment configuration lives in YAML
files. Code loads config; code does not contain config.

**Jinja2 for prompt templating.** Prompt `.md` files use `{{ variable }}` syntax.
The `prompt_loader.py` module injects file contents, pylint reports, corpus text,
and other context before sending to Ollama.

**Base schema inheritance.** Every experiment config overrides only what differs
from `data/experiment_base.yaml`. The loader merges them at runtime.

**Corpus sources are flexible.** The experiment runner accepts both `url` and
`file` source types for corpus text. Both land in `{{ source_text }}` identically.
Prompt templates never know the difference.

**Model digests are pinned after first run.** Fill in the `digest` field in each
experiment config after the first run:
```bash
ollama show gemma4:e2b --verbose
ollama show gemma4:e4b --verbose
```

**SQL is never auto-applied.** Experiment 06 output is staged SQL only. A human
reviews each block, assigns difficulty, verifies IDs, and pastes into Adminer.

---

## Future: Designing Gemma Webapp (v2.0)

The structure of this repo is designed to be wrapped in a web UI. Key features
planned for v2.0:

- Dual-listbox experiment selector (available → run queue)
- Numeric prefix auto-assigned by the system
- Voice selection for capstone summary and readme
- Community voice submissions via PR workflow
- PostgreSQL read model synced from YAML run logs
- CRUD interface for experiment configs
- "Are you interested in playing?" interest form for community contributors
- Ankh-Morpork corpus + Pratchett voice

See Obsidian notes for full v2.0 feature spec.

```
