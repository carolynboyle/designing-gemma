# config.yaml

**Path:** experiments/06_srb_sentence_gen/config.yaml
**Syntax:** yaml
**Generated:** 2026-05-13 07:45:45

```yaml
# =============================================================================
# experiments/06_srb_sentence_gen/config.yaml
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
# Three corpora, one per capstone voice. Each yields one staged SQL file
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
  - label: hitchhiker
    voice: hitchhiker
    source_type: file
    source: corpora/hhg_excerpt.txt     # library/preview excerpt — see note below
    status: active
    note: >
      Douglas Adams, The Hitchhiker's Guide to the Galaxy. Not public domain.
      Excerpt copied from library copy or Amazon preview for personal/educational
      use. Not redistributed. Long, elaborately modified sentences; rich
      prepositional structure. Skews medium/hard difficulty.

  - label: metamorphosis
    voice: kafka
    source_type: url
    source: https://www.gutenberg.org/files/5200/5200-0.txt
    status: active
    note: >
      Franz Kafka, The Metamorphosis (English translation). Public domain via
      Project Gutenberg. Dense, formally structured sentences; good subordinate
      clause examples for future schema extension. Lands across difficulty range.

  - label: terminator
    voice: annihilator
    source_type: file
    source: corpora/terminator_excerpt.txt   # short excerpt for personal use
    status: active
    note: >
      The Terminator (1984) screenplay. Not public domain. Short excerpt for
      personal/educational use. Terse, imperative sentences; minimal modifiers.
      Skews easy/medium difficulty. Strong contrast with Adams and Kafka corpora.

  - label: ankh_morpork
    voice: pratchett
    source_type: file
    source: corpora/ankh_morpork_excerpt.txt
    status: pending                     # future — voice not yet defined
    note: >
      Terry Pratchett, Discworld series. Future experiment. Pratchett voice
      to be added to voices.yaml when this corpus is activated. Grammatically
      impeccable, philosophically unsettling. The Patrician approves.

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
