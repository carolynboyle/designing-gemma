# schema_staging.sql

**Path:** data/schema_staging.sql
**Syntax:** sql
**Generated:** 2026-05-12 08:55:21

```sql
-- =============================================================================
-- Sr. Barbara's Class - Staging Schema
-- =============================================================================
-- Holds Gemma-generated sentences pending human review before promotion
-- to the production schema (public).
--
-- Lookup tables (difficulty_levels, parts_of_speech) are shared with the
-- public schema. No duplication needed — staging tables reference them directly.
--
-- Workflow:
--   1. Gemma output lands in results/ as staged SQL targeting this schema
--   2. Human pastes SQL blocks into Adminer — rows enter staging
--   3. Human reviews, assigns difficulty, sets review_status = 'approved'
--   4. Run promote_staging.sql to move approved rows to public schema
--   5. Run reset_staging.sql (optional) to clear promoted rows from staging
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS staging;

-- -----------------------------------------------------------------------------
-- staging.sentences
-- Mirrors public.sentences with added review metadata columns.
-- id is human-assigned with an offset from the production max to avoid
-- collisions. Use the ID offset queries in experiment 06 config before each run.
-- -----------------------------------------------------------------------------

CREATE TABLE staging.sentences (
    id                INTEGER PRIMARY KEY,
    difficulty_id     INTEGER REFERENCES public.difficulty_levels(id),
    submitted_at      TIMESTAMP DEFAULT NOW(),
    submitted_by      TEXT DEFAULT 'gemma4',
    model             TEXT,              -- which Ollama model generated this row
    prompt_label      TEXT,              -- unguided | guided
    corpus_label      TEXT,              -- hitchhiker | metamorphosis | terminator
    run_id            TEXT,              -- links back to run_log.yaml entry
    review_status     TEXT DEFAULT 'pending'
                      CHECK (review_status IN ('pending', 'approved', 'rejected')),
    reviewer_notes    TEXT
);

-- -----------------------------------------------------------------------------
-- staging.sentence_parts
-- Mirrors public.sentence_parts. References staging.sentences.
-- -----------------------------------------------------------------------------

CREATE TABLE staging.sentence_parts (
    id                INTEGER PRIMARY KEY,
    sentence_id       INTEGER REFERENCES staging.sentences(id),
    part_of_speech_id INTEGER REFERENCES public.parts_of_speech(id),
    position          INTEGER NOT NULL
);

-- -----------------------------------------------------------------------------
-- staging.sentence_tokens
-- Mirrors public.sentence_tokens. References staging.sentence_parts.
-- Token IDs use SERIAL — no explicit ID needed in Gemma output.
-- -----------------------------------------------------------------------------

CREATE TABLE staging.sentence_tokens (
    id                SERIAL PRIMARY KEY,
    sentence_part_id  INTEGER REFERENCES staging.sentence_parts(id),
    part_of_speech_id INTEGER REFERENCES public.parts_of_speech(id),
    token             VARCHAR(100) NOT NULL,
    position          INTEGER NOT NULL
);

```
