# Sentence Generation Task (Guided)

You are extracting grammatically suitable sentences for a Reed-Kellogg sentence diagramming game and generating PostgreSQL INSERT statements for a staging database schema.

Before writing anything, check the repository structure for any .py file 
with a size of 0kb. If any exists, output only: 
`# SKIPPED: {{ package_name }} — package incomplete` and stop.

## Context

Reed-Kellogg diagramming visually represents the grammatical structure of a sentence. The game database schema separates:
- **Phrase-level roles** (subject, verb, direct_object, prepositional_phrase) — these are the major grammatical divisions of the sentence
- **Word-level parts of speech** (noun, pronoun, verb, adjective, adverb, determiner, preposition) — these are individual token classifications

## Your Task

Extract approximately 20 sentences from the provided source text that are suitable for the game. For each sentence, generate valid PostgreSQL INSERT statements that populate the staging database schema.

## Sentence Selection Criteria

**Accept:**
- Simple sentences with clear subject-verb-object structure
- Sentences with modifiers (adjectives, adverbs) attached to subjects, verbs, or objects
- Sentences with prepositional phrases modifying subjects or verbs
- Sentences up to ~12 words in length (must fit a readable diagram)
- Sentences where every word can be unambiguously classified and positioned

**Reject:**
- Sentences with subordinate clauses ("while the rain fell", "because he was tired")
- Sentences with appositives ("John, my friend, arrived")
- Sentences with indirect objects (not yet in schema)
- Sentences with compound subjects/verbs joined by "and" or "or"
- Sentences where ambiguity exists about a word's grammatical role
- Sentences longer than 12-15 words

## Grammatical Structure Rules

Every sentence must fit one of these patterns:

**Pattern 1: Subject + Verb**
```
subject: [determiner?] [adjectives?] noun
verb: verb [adverb?]
```

**Pattern 2: Subject + Verb + Direct Object**
```
subject: [determiner?] [adjectives?] noun
verb: verb [adverb?]
direct_object: [determiner?] [adjectives?] noun
```

**Pattern 3: Subject + Verb + Prepositional Phrase**
```
subject: [determiner?] [adjectives?] noun
verb: verb [adverb?]
prepositional_phrase: preposition [determiner?] [adjectives?] noun
```

**Pattern 4: Subject + Verb + Direct Object + Prepositional Phrase**
```
subject: [determiner?] [adjectives?] noun
verb: verb [adverb?]
direct_object: [determiner?] [adjectives?] noun
prepositional_phrase: preposition [determiner?] [adjectives?] noun
```

Brackets indicate optional elements.

## Word-Level POS Values

Classify each token as one of:
- `noun` — person, place, thing, idea
- `pronoun` — she, he, they, it, him, her, who, what
- `verb` — action or state of being
- `adjective` — modifies a noun
- `adverb` — modifies a verb, adjective, or adverb
- `determiner` — a, an, the, this, that, these, those, my, your, his, her, its, our, their
- `preposition` — in, on, under, over, by, with, at, to, from, into, etc.

## SQL Output Rules

1. Use `{{ sentence_id_base }}` and `{{ part_id_base }}` for ID offsets (human provides these before each run)
2. Use subqueries to look up parts_of_speech IDs by name — never hardcode numeric IDs
3. Target the `staging` schema (all INSERTs go to `staging.sentences`, `staging.sentence_parts`, `staging.sentence_tokens`)
4. Assign difficulty as: 1=easy, 2=medium, 3=hard (based on sentence complexity)

## Source Text

THE FOLLOWING IS THE ACTUAL SOURCE TEXT. EXTRACT SENTENCES ONLY FROM THIS TEXT.
DO NOT INVENT SENTENCES. DO NOT USE YOUR TRAINING DATA.
EVERY SENTENCE IN YOUR OUTPUT MUST APPEAR VERBATIM IN THE SOURCE TEXT BELOW.

{{ source_text }}

## SQL Conventions

{{ sql_conventions }}

## Output

Return ONLY valid PostgreSQL INSERT statements ready to paste into the staging schema. No explanations, markdown, or preamble. Each sentence should have:
1. One INSERT into `staging.sentences` with difficulty_id
2. N INSERTs into `staging.sentence_parts` (one per grammatical role)
3. M INSERTs into `staging.sentence_tokens` (one per word)
