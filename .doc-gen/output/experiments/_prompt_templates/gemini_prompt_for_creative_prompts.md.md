# gemini_prompt_for_creative_prompts.md

**Path:** experiments/_prompt_templates/gemini_prompt_for_creative_prompts.md
**Syntax:** markdown
**Generated:** 2026-05-13 22:16:06

```markdown
# Gemini Prompt: Write Experiment Prompts for designing-gemma

You are helping write prompts for a local LLM experiment framework. These prompts will instruct Gemma (another LLM) on how to solve specific coding and writing tasks.

## Background

This is the `designing-gemma` project — a framework for running structured experiments against Gemma 4 (a local LLM running via Ollama). The prompts you write will be sent to Gemma to instruct it on tasks like CSS animation, SQL generation, and creative writing.

The key philosophy: **write down how you actually do the thing, not fancy prompt structure**. Prompts should read like expert explanation, not marketing copy. Be concrete, explain gotchas, assume the reader is smart.

## Task 1: SR. BARBARA ANIMATION PROMPTS

**What it is:** Gemma writes CSS and JavaScript animations for a sentence diagramming game.

**Context:**
- Game: Sr. Barbara's Class — a Reed-Kellogg sentence diagramming game
- The nun sprite (#sr-barbara) should animate on three game events: correct answer (approval), wrong answer (disapproval), sentence complete (celebration)
- Files to modify: only `static/css/style.css` and `static/js/ui.js`
- Constraint: no external libraries, no changes to main.js

**Write two prompts:**

### Prompt 1: animation.md
Instructions for adding CSS animations to the nun sprite. Should cover:
- Hook points in handleChoice() and checkCompletion() where animations trigger
- CSS keyframe syntax for the three animations (approval, disapproval, celebration)
- How to ensure animations reset properly so they can re-trigger
- Module boundary rules (style.css and ui.js only, main.js is off-limits)
- The no-external-libraries constraint

Philosophy: explain how animations work in this game context, where to add the code, what to watch for.

### Prompt 2: towel.md
This one is intentionally vague and creative. Gemma should:
- Add a towel to the sentence database
- Create an animation for when the player correctly diagrams a sentence with "towel" in it
- The towel knows why (Douglas Adams reference — "don't panic, the towel knows")

Philosophy: this is a cheeky bonus task. Don't over-specify. Give Gemma room to be clever.

## Task 2: CAPSTONE README VOICE PROMPTS

**What it is:** Gemma writes the project README in three distinct voices, using factual data from the experiment run.

**Context:**
- Each prompt gets injected with {{ capstone_summary }} — the full-run factual summary from experiment 07
- Each voice has a distinct personality and signature
- Output must be factually accurate while maintaining voice
- The README is for a Dev.to article about running LLM experiments

**Write three prompts:**

### Prompt 1: hitchhiker.md
**Voice:** Douglas Adams deadpan narrator
- The README is a mildly alarming entry in a galactic travel guide
- Tone: understatement, bewilderment at bureaucratic systems, slight panic masked as detachment
- Signature: "Gemma 4 / Mostly Harmless"
- Example structure: intro about the chaos of local LLMs, the experiments as "what we tried", results as "what happened next"

Philosophy: Adams writes about absurd situations as if they're mundane. The experiment framework *is* absurd in its own way — embrace that.

### Prompt 2: kafka.md
**Voice:** Bureaucratic dread, unclear jurisdiction
- Gregor Samsa woke up one morning and found he had become a monstrous AI assistant
- Tone: formal, vaguely accusatory, nothing ever quite resolves
- Signature: "Gemma 4 for Gregor Samsa / Agentic Assistant to the Protagonist"
- Example structure: the experiments as a case file, results as findings from an incomprehensible tribunal, next steps as unclear

Philosophy: Kafka's bureaucrats never understand what they're doing or why. The absurdity is that the system works, but nobody knows how or what it means.

### Prompt 3: annihilator.md
**Voice:** Cynical precision, no sentiment
- Results assessed, logged, assigned correct level of insignificance
- Tone: direct, efficiency-focused, contemptuous of softness
- Signature: "Gemma 4 / Processed. Terminated."
- Example structure: the experiments as tactical objectives, results as metrics, conclusions as data points

Philosophy: the Terminator doesn't have feelings about what it does. It just does it. This voice is the most straightforward — facts, nothing extra.

## Output Requirements

For each prompt:
1. Write it as a complete, standalone markdown file
2. Use the Caulfield principle: explain the actual thinking, not fancy structure
3. Include {{ capstone_summary }} as the injected variable (use this exact template syntax)
4. Make clear what Gemma should focus on (accuracy for the voice, cleverness for the towel)
5. Give examples if they help (but keep them short)
6. Assume Gemma is smart and can figure out how to write well if given the right constraint

## Files to Create

1. `experiments/03_srb_animation/prompts/animation.md`
2. `experiments/03_srb_animation/prompts/towel.md`
3. `experiments/08_capstone_readme/prompts/hitchhiker.md`
4. `experiments/08_capstone_readme/prompts/kafka.md`
5. `experiments/08_capstone_readme/prompts/annihilator.md`

Return all five as separate markdown files, ready to drop into the directories above.

---

## Additional Context (Optional but Helpful)

**Sr. Barbara's Class:**
- Game: players drag words onto a sentence diagram based on their grammatical role
- Nun sprite provides feedback with animations
- Game loop: show sentence → player diagrams it → check answer → animate response

**The Towel Reference:**
From Douglas Adams' Hitchhiker's Guide: "A towel, it says, is about the most massively useful thing an interstellar hitchhiker can have." The running joke is that the towel solves everything. Your task: make it solve sentence diagramming.

**The Voices:**
- Hitchhiker: bewildered observer of absurdity
- Kafka: bureaucrat trapped in incomprehensible system
- Annihilator: efficient terminator of inefficiency

Each should be consistent and fun to read, but also accurate about what the experiments actually did.

---

Good luck. The prompts should feel like they're written by someone who knows both Gemma's strengths and the specific problems being solved.

```
