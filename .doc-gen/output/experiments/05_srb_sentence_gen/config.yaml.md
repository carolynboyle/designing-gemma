# config.yaml

**Path:** experiments/05_srb_sentence_gen/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-15 14:53:19

```yaml
# =============================================================================
# experiments/05_srb_sentence_gen/config.yaml
# Sr. Barbara sentence generation experiment — overrides experiment_base.yaml
#
# Target: sr-barbara repo (Postgres database via Adminer)
# Goal: Extract grammatically suitable sentences from source corpora and
#       generate valid PostgreSQL INSERT statements for the game database.
#
# RISK: None — output is staged SQL only. Nothing touches the database
# until a human reviews and pastes selected blocks into Adminer manually.
#
# Two prompt variants:
#   unguided — schema inferred from worked examples only
#   guided   — full schema spec and constraints provided explicitly
#
# Four corpora, public domain prose. Each yields one staged SQL file
# per model per prompt variant.
# =============================================================================

experiment:
  name: srb_sentence_gen
  description: >
    Ask Gemma to extract grammatically suitable sentences from provided source
    text and generate valid PostgreSQL INSERT statements for the Sr. Barbara's
    Class sentence diagramming game. Tests Gemma as a domain-aware structured
    data generator. Output is staged SQL reviewed and selectively applied by
    a human via Adminer. Never auto-applied.
  experiment_version: 1
  target_repo: https://github.com/carolynboyle/sr-barbara
  target_branch: ~               # read-only generative task — no branch needed

model:
  temperature: 0.3               # slightly higher than mechanical tasks —
                                 # Gemma needs flexibility to interpret grammar
                                 # but output must still be structured SQL

prompts:
  prompt_dir: prompts/
  prompts:
    - file: unguided.md
      label: unguided
      description: >
        Source text + three worked SQL examples from seed.sql. Gemma infers
        schema from examples. No explicit POS lists or phrase role constraints.
        Tests structural inference from examples alone.
    - file: guided.md
      label: guided
      description: >
        Everything in unguided plus: full list of valid phrase roles, full list
        of valid token-level POS values, explicit sentence selection criteria,
        difficulty placeholder instruction. Tests instruction-following precision
        under full specification.

# =============================================================================
# corpora
# Source texts injected as {{ source_text }} via Jinja2.
# source_type: url  — Python script fetches content before injection
# source_type: file — Python script reads local file before injection
# Both land in {{ source_text }} identically. Prompts never know the difference.
#
# Human pre-run step: execute ID offset queries in Adminer before each run.
# Results are passed as {{ sentence_id_base }} and {{ part_id_base }}.
#
#   SELECT (floor(MAX(id) / 1000) + 1) * 1000 FROM sentences;
#   SELECT (floor(MAX(id) / 1000) + 1) * 1000 FROM sentence_parts;
# =============================================================================

corpora:
  - label: wodehouse
    source_type: file
    source: corpora/wodehouse
    status: active
    note: >
      P.G. Wodehouse, Love Among the Chickens. Public domain.
      Chapter 3. Absurdist comic prose, varied sentence structures,
      good mix of dialogue and narration. Skews medium difficulty.

  - label: austen
    source_type: file
    source: corpora/austen
    status: active
    note: >
      Jane Austen, Pride and Prejudice. Public domain.
      Chapter 1. Formal prose, complex subordinate clauses,
      excellent variety of sentence structures. Skews medium/hard.

  - label: doyle
    source_type: file
    source: corpora/doyle
    status: active
    note: >
      Arthur Conan Doyle, The Red-Headed League. Public domain.
      The deduction scene. Mix of dialogue, narration, and Holmes's
      reasoning. Good variety of sentence types. Skews medium.

  - label: kafka
    source_type: file
    source: corpora/kafka
    status: active
    note: >
      Franz Kafka, The Metamorphosis. Public domain via Project Gutenberg.
      Dense, formally structured sentences. Skews medium/hard.

# =============================================================================
# sql_conventions
# Documents the SQL output conventions Gemma must follow.
# Injected into prompts as {{ sql_conventions }} for reference.
# =============================================================================

sql_conventions:
  target_schema: staging                   # all INSERTs target staging schema
                                           # never public — promotion via promote_staging.sql
  id_offset:
    sentences: "{{ sentence_id_base }}"    # human queries Adminer before each run
    parts: "{{ part_id_base }}"            # human queries Adminer before each run
  id_offset_queries: |
    SELECT (floor(MAX(id) / 1000) + 1) * 1000 FROM staging.sentences;
    SELECT (floor(MAX(id) / 1000) + 1) * 1000 FROM staging.sentence_parts;
  pos_lookup: subquery                     # never hardcoded numeric IDs
  sequence_reset: false                    # staging uses explicit IDs not sequences
  target_sentences: 20                     # per run
  difficulty_assignment: human             # Gemma does not classify difficulty
                                           # reviewer sets difficulty_id before promoting

results:
  results_dir: results/
  output: per_run                          # one staged SQL file per model/prompt/corpus

```
