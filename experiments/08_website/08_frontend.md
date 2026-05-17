# Dashboard Frontend Task

You are the Frontend UI Developer on a small development team. The
Lead Architect has already written the backend build script. Your
single task is to replace the `generate_ui_chassis()` placeholder
function with a complete implementation.

## YOUR TASK IS NARROWLY SCOPED

You are writing ONE Python function: `generate_ui_chassis()`.
Do not rewrite anything else in the script. Do not touch the
`parse_experiments()`, `generate_fragments()`, or `main()` functions.
Do not write a new script. Replace only the placeholder.

## The Architect's Script (Your Context)

{{ architect_output }}

## What generate_ui_chassis() Must Do

The function receives:
- `experiments_list` — a list of experiment dicts (already parsed)
- `dist_dir` — a `pathlib.Path` pointing to the `dist/` output directory

It must write `dist/index.html` — the complete kanban dashboard.

## index.html Layout

```
┌─────────────────────────────────────────────────────────────┐
│  designing-gemma · Experiment Dashboard        [theme toggle]│
├──────────────────┬──────────────────────────────────────────┤
│  Experiments     │                                          │
│  ─────────────   │                                          │
│  01 · readme_gen │   ← #detail-viewport                     │
│  02a · linter    │                                          │
│  02b · linter d  │   Placeholder: "Select an experiment"    │
│  03 · animation  │                                          │
│  04 · restructure│                                          │
│  05 · sentence   │                                          │
│  06 · summary    │                                          │
│  07 · readme     │                                          │
│  08 · dashboard  │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

## Required HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>designing-gemma · Experiment Dashboard</title>
  <link id="theme" rel="stylesheet" href="themes/e2b.css">
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <style>
    /* YOUR CSS GOES HERE — use :root variables from the theme files */
    /* Do not hardcode colors — use var(--bg-main), var(--accent), etc. */
  </style>
</head>
<body>
  <header>
    <h1>designing-gemma · Experiment Dashboard</h1>
    <button id="theme-toggle" onclick="toggleTheme()">
      Switch to e4b theme
    </button>
  </header>

  <div class="dashboard">
    <aside class="sidebar">
      <!-- experiment buttons generated from experiments_list -->
    </aside>
    <main id="detail-viewport">
      <div class="placeholder">
        <h2>designing-gemma</h2>
        <p>Select an experiment from the list to review its
           design, prompts, and results.</p>
      </div>
    </main>
  </div>

  <script>
    let currentTheme = 'e2b';
    function toggleTheme() {
      currentTheme = currentTheme === 'e2b' ? 'e4b' : 'e2b';
      document.getElementById('theme').href =
        `themes/${currentTheme}.css`;
      document.getElementById('theme-toggle').textContent =
        `Switch to ${currentTheme === 'e2b' ? 'e4b' : 'e2b'} theme`;
    }
  </script>
</body>
</html>
```

## Sidebar Button Format

One button per experiment. Button text: `{number} · {name} · {RISK}`

```html
<button class="experiment-btn enabled"
        hx-get="fragments/01_readme_gen.html"
        hx-target="#detail-viewport"
        hx-swap="innerHTML">
  01 · readme_gen · NONE
</button>
```

Disabled experiments get class `disabled` instead of `enabled` and
are rendered after enabled ones, visually muted.

## CSS Requirements

Use CSS Grid for the two-panel layout. Both panels scroll independently.
Full viewport height. Clean developer tool aesthetic — not a marketing
page. All colors via CSS custom properties (`var(--name)`) defined in
the theme files. You may define layout, spacing, and typography values
directly in the `<style>` block — but never hardcode colors.

CSS variable names the theme files will define:
```css
--bg-main        /* main background */
--bg-sidebar     /* sidebar background */
--bg-header      /* header background */
--text-primary   /* primary text */
--text-muted     /* secondary/muted text */
--accent         /* active/selected state */
--border         /* dividers and borders */
--btn-bg         /* experiment button background */
--btn-hover      /* button hover state */
--btn-active     /* selected button */
--code-bg        /* background for code/pre blocks */
--badge-none     /* risk badge: none */
--badge-low      /* risk badge: low */
--badge-medium   /* risk badge: medium */
--badge-high     /* risk badge: high */
--status-complete
--status-bailed
--status-failed
--status-pending
```

## Output

Return ONLY the replacement `generate_ui_chassis()` function —
complete, from `def generate_ui_chassis(` to the closing line.
No explanations. No other functions. Ready to paste directly into
`build.py` replacing the placeholder.
