# promote_staging.sql

**Path:** data/promote_staging.sql
**Syntax:** sql
**Generated:** 2026-05-12 08:55:21

```sql
-- =============================================================================
-- Sr. Barbara's Class - Promote Staging to Production
-- =============================================================================
-- Moves approved sentences from staging schema to public (production) schema.
--
-- Prerequisites:
--   1. Review staging.sentences in Adminer
--   2. Assign difficulty_id for each row (edit the value directly in Adminer)
--   3. Set review_status = 'approved' for rows to promote
--   4. Run this script
--
-- Safe to run multiple times — only promotes rows with review_status = 'approved'
-- that do not already exist in public.sentences (ON CONFLICT DO NOTHING).
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Promote sentences
-- -----------------------------------------------------------------------------

INSERT INTO public.sentences (id, difficulty_id, created_at)
SELECT
    s.id,
    s.difficulty_id,
    s.submitted_at
FROM staging.sentences s
WHERE s.review_status = 'approved'
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Promote sentence_parts
-- -----------------------------------------------------------------------------

INSERT INTO public.sentence_parts (id, sentence_id, part_of_speech_id, position)
SELECT
    sp.id,
    sp.sentence_id,
    sp.part_of_speech_id,
    sp.position
FROM staging.sentence_parts sp
JOIN staging.sentences s ON sp.sentence_id = s.id
WHERE s.review_status = 'approved'
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Promote sentence_tokens
-- -----------------------------------------------------------------------------

INSERT INTO public.sentence_tokens (sentence_part_id, part_of_speech_id, token, position)
SELECT
    st.sentence_part_id,
    st.part_of_speech_id,
    st.token,
    st.position
FROM staging.sentence_tokens st
JOIN staging.sentence_parts sp ON st.sentence_part_id = sp.id
JOIN staging.sentences s ON sp.sentence_id = s.id
WHERE s.review_status = 'approved'
ON CONFLICT DO NOTHING;

-- -----------------------------------------------------------------------------
-- Mark promoted rows as promoted in staging
-- -----------------------------------------------------------------------------

UPDATE staging.sentences
SET review_status = 'promoted'
WHERE review_status = 'approved';

-- -----------------------------------------------------------------------------
-- Reset sequences after promotion
-- -----------------------------------------------------------------------------

SELECT setval('sentences_id_seq',
    (SELECT COALESCE(MAX(id), 1) FROM public.sentences));

SELECT setval('sentence_parts_id_seq',
    (SELECT COALESCE(MAX(id), 1) FROM public.sentence_parts));

COMMIT;

-- -----------------------------------------------------------------------------
-- Verify promotion
-- -----------------------------------------------------------------------------

SELECT
    s.id,
    dl.level AS difficulty,
    string_agg(st.token, ' ' ORDER BY sp.position, st.position) AS sentence
FROM public.sentences s
JOIN public.difficulty_levels dl ON s.difficulty_id = dl.id
JOIN public.sentence_parts sp ON sp.sentence_id = s.id
JOIN public.sentence_tokens st ON st.sentence_part_id = sp.id
WHERE s.id IN (
    SELECT id FROM staging.sentences WHERE review_status = 'promoted'
)
GROUP BY s.id, dl.level
ORDER BY s.id;

```
