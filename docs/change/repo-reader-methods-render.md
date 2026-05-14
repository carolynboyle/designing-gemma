# Changeset: repo_reader.py — render methods in `_format_python_entry()`
## File: `src/designing_gemma/repo_reader.py`

---

### Overview

`_format_python_entry()` renders the skeleton dict for a Python file into
the text block Gemma receives as `{{ repo_context }}`. It currently renders
`imports`, `classes`, and `functions` but has no awareness of the new
`methods` key added by `SkeletonExtractor`. This change adds `methods`
rendering between `classes` and `functions`, matching the existing pattern.

Backward compatible — if `methods` is absent or empty (e.g. older `.skel`
files), nothing is rendered for that section.

---

### Change 1 — Add `methods` rendering to `_format_python_entry()`

**BEFORE:**
```python
    classes = entry.get("classes", [])
    if classes:
        lines.append(f"classes: {', '.join(classes)}")
    else:
        lines.append("classes: (none)")

    functions = entry.get("functions", [])
    if functions:
        lines.append("functions:")
        for fn in functions:
            lines.append(f"  {fn}")
    else:
        lines.append("functions: (none)")
```

**AFTER:**
```python
    classes = entry.get("classes", [])
    if classes:
        lines.append(f"classes: {', '.join(classes)}")
    else:
        lines.append("classes: (none)")

    methods = entry.get("methods", [])
    if methods:
        lines.append("methods:")
        for method in methods:
            lines.append(f"  {method}")

    functions = entry.get("functions", [])
    if functions:
        lines.append("functions:")
        for fn in functions:
            lines.append(f"  {fn}")
    else:
        lines.append("functions: (none)")
```

**Why:** Methods are now extracted separately from top-level functions by
`SkeletonExtractor`. Without this change, Gemma would see class names but
no method signatures — exactly the problem we set out to fix. The `methods`
block is omitted entirely when empty rather than printing `methods: (none)`,
since a file with no classes naturally has no methods and the absence is
already implied.
