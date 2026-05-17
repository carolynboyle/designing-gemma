# Color Palette Task

You have been part of a development team building a dashboard website
for the designing-gemma experiment framework.

designing-gemma is a structured evaluation framework for Gemma 4 edge
models running locally via Ollama. It runs experiments that test what
small language models can actually do — code cleanup, animation
generation, sentence generation, README writing, and package
restructuring. The experiments revealed distinct personality differences
between models: some fail silently, some hallucinate confidently, some
do exactly what they're told on simple tasks and fall apart on complex
ones. The framework captures all of this in structured run logs.

The dashboard you helped build displays these experiments and their
results side by side for human review.

## Your Task

Choose a color palette for this dashboard that reflects the nature of
the project. This is a developer tool for evaluating AI models — not
a marketing page, not a consumer app. The people using it are
programmers reviewing experiment results.

Make a genuine choice. Consider what the project is about:
edge models, local inference, structured evaluation, failure modes,
the contrast between confident hallucination and calibrated refusal.

## What To Deliver

1. **A brief explanation** (3-5 sentences) of why you chose this
   palette and what it reflects about the project.

2. **A complete CSS `:root` block** defining these exact variables:

```css
:root {
  --bg-main:        /* main content area background */
  --bg-sidebar:     /* sidebar background */
  --bg-header:      /* header bar background */
  --text-primary:   /* primary text color */
  --text-muted:     /* secondary/muted text */
  --accent:         /* active/selected state, links */
  --border:         /* dividers and borders */
  --btn-bg:         /* experiment button default background */
  --btn-hover:      /* button hover state */
  --btn-active:     /* currently selected button */
  --code-bg:        /* background for code/pre blocks */
  --badge-none:     /* risk badge color: NONE risk */
  --badge-low:      /* risk badge color: LOW risk */
  --badge-medium:   /* risk badge color: MEDIUM risk */
  --badge-high:     /* risk badge color: HIGH risk */
  --status-complete:  /* run status: complete */
  --status-bailed:    /* run status: bailed (model emitted 0 tokens) */
  --status-failed:    /* run status: failed */
  --status-pending:   /* run status: pending */
}
```

## Format

Return your explanation first, then the CSS block.
The CSS block should be ready to save directly as a `.css` file.
No other output.
