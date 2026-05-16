# unguided.md

**Path:** experiments/05_srb_sentence_gen/prompts/unguided.md
**Syntax:** markdown
**Generated:** 2026-05-15 14:53:19

```markdown
# Sentence Generation Task (Unguided)

You are extracting grammatically suitable sentences for a Reed-Kellogg sentence diagramming game.

## Context

Reed-Kellogg diagramming is a visual method for showing the grammatical relationships in a sentence. The game represents sentences as a diagram with tokens positioned by their grammatical role.

## Your Task

From the provided source text, extract approximately 20 sentences that are suitable for the game. For each sentence, generate valid PostgreSQL INSERT statements.

## What Works

Study these worked examples to infer the pattern:

**Example 1: "Birds fly."**
- Simple structure: subject + verb
- Every word is placed on the diagram in its role

**Example 2: "The young baker made bread."**
- Subject with modifiers (determiner + adjective + noun)
- Verb
- Direct object (noun)

**Example 3: "Rain fell on the roof."**
- Subject
- Verb
- Prepositional phrase (preposition + determiner + object of preposition)

**Example 4: "The old man slept soundly under the oak tree."**
- Subject with modifiers
- Verb with adverb modifier
- Prepositional phrase

## What Doesn't Work

- Sentences with subordinate clauses ("while the rain fell")
- Sentences with appositives ("John, my friend, left")
- Sentences with indirect objects (not yet in schema)
- Sentences so complex they don't fit the visual diagram clearly

## Output Format

Generate PostgreSQL INSERT statements in this exact format. You may infer the SQL structure from the examples, but the key rules are:

1. Create one row in `sentences` with a difficulty level (1=easy, 2=medium, 3=hard)
2. Create rows in `sentence_parts` for each grammatical role in the sentence
3. Create rows in `sentence_tokens` for each individual word, tagged with its word-level POS

Use subqueries to look up parts_of_speech IDs by name. Never hardcode numeric IDs.

Valid word-level POS values:
- noun, pronoun, verb, adjective, adverb, determiner, preposition

Valid phrase-level POS values (used in sentence_parts):
- subject, verb, direct_object, prepositional_phrase, object_of_preposition

## Source Text

THE FOLLOWING IS THE ACTUAL SOURCE TEXT. EXTRACT SENTENCES ONLY FROM THIS TEXT.
DO NOT INVENT SENTENCES. DO NOT USE YOUR TRAINING DATA.
EVERY SENTENCE IN YOUR OUTPUT MUST APPEAR VERBATIM IN THE SOURCE TEXT BELOW.

{{ source_text }}

## Output

Return ONLY valid PostgreSQL INSERT statements. No explanations, no markdown, no preamble. The statements should be ready to paste directly into a PostgreSQL client.

```
