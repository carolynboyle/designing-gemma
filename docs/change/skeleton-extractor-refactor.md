# Changeset: skeleton_reader.py — SkeletonExtractor class
## File: `src/designing_gemma/skeleton_reader.py`

---

### Overview

Replaces the standalone `_extract_python_skeleton()` function with a
`SkeletonExtractor` class. The class uses the working parts of the
original `ast.walk()` approach for imports, adds an explicit two-pass
method for class and method extraction, and keeps top-level function
extraction separate. Also adds `class_list.txt` debug output and
cleanup on run start.

---

### Change 1 — Add `CLASS_LIST_PATH` constant

**Why:** Single source of truth for the debug file location. Repo root,
gitignored, overwritten each run.

**BEFORE** (after existing constants block, line 37):
```python
DEFAULT_SIZE_LIMIT    = 5000   # characters — non-Python files above this are excluded


class SkeletonError(Exception):
```

**AFTER:**
```python
DEFAULT_SIZE_LIMIT    = 5000   # characters — non-Python files above this are excluded
CLASS_LIST_PATH       = "class_list.txt"   # debug output, repo root, gitignored


class SkeletonError(Exception):
```

---

### Change 2 — Replace `_extract_python_skeleton()` with `SkeletonExtractor` class

**Why:** The original single-pass `ast.walk()` with an `elif` chain
silently drops class methods because once a `ClassDef` is matched, its
child `FunctionDef` nodes compete with the same `elif` chain in
subsequent iterations — the relationship between class and method is
never established. The new class uses three focused methods:

- `extract_imports()` — the original `ast.walk()` import logic, unchanged
- `extract_classes_and_methods()` — explicit two-pass: find `ClassDef`
  nodes in `tree.body`, then walk each class body for methods
- `extract_top_level_functions()` — only functions directly in
  `tree.body`, not inside any class
- `extract()` — coordinator; calls all three and returns combined dict

**BEFORE** (lines 56–110):
```python
def _extract_python_skeleton(source: str) -> dict:
    """
    Parse Python source with ast and extract imports, classes, functions.

    Args:
        source: Python source code as a string.

    Returns:
        Dict with keys: imports (list[str]), classes (list[str]),
        functions (list[str]).

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    tree = ast.parse(source)

    imports   = []
    classes   = []
    functions = []

    for node in ast.walk(tree):
        # Import statements: import os, import pathlib
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.asname or alias.name)

        # From imports: from pathlib import Path
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname or alias.name
                imports.append(f"{module}.{name}" if module else name)

        # Top-level class definitions only
        elif isinstance(node, ast.ClassDef):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        # Top-level and class-level function definitions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Build signature string
            args = node.args
            arg_names = [a.arg for a in args.args]
            if args.vararg:
                arg_names.append(f"*{args.vararg.arg}")
            if args.kwarg:
                arg_names.append(f"**{args.kwarg.arg}")
            sig = f"{node.name}({', '.join(arg_names)})"
            functions.append(sig)

    return {
        "imports":   sorted(set(imports)),
        "classes":   classes,
        "functions": functions,
    }
```

**AFTER:**
```python
class SkeletonExtractor:
    """
    Extracts structural summaries from Python source using the ast module.

    Three focused extraction passes — imports, classes+methods, top-level
    functions — are coordinated by extract(), which returns a single dict
    suitable for inclusion in the manifest.skel output.

    Also writes class_list.txt to the repo root for debugging. This file
    is gitignored and overwritten at the start of each build_skeleton() run.
    """

    def __init__(self, source: str):
        """
        Args:
            source: Python source code as a string.

        Raises:
            SyntaxError: If the source cannot be parsed.
        """
        self.tree = ast.parse(source)

    @staticmethod
    def _build_signature(node) -> str:
        """Build a readable signature string from a FunctionDef node."""
        args = node.args
        arg_names = [a.arg for a in args.args]
        if args.vararg:
            arg_names.append(f"*{args.vararg.arg}")
        if args.kwarg:
            arg_names.append(f"**{args.kwarg.arg}")
        return f"{node.name}({', '.join(arg_names)})"

    def extract_imports(self) -> list[str]:
        """
        Walk the full tree for import statements.

        Returns:
            Sorted, deduplicated list of import names/aliases.
        """
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.append(f"{module}.{name}" if module else name)
        return sorted(set(imports))

    def extract_classes_and_methods(self) -> tuple[list[str], list[str]]:
        """
        Two-pass extraction of classes and their methods.

        Pass 1: find ClassDef nodes directly in tree.body.
        Pass 2: for each class, walk its body for FunctionDef nodes,
                building ClassName.method(args) signatures.

        Returns:
            Tuple of (class_names, method_signatures) where method_signatures
            entries are formatted as "ClassName.method_name(args)".
        """
        class_names = []
        methods = []

        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = self._build_signature(item)
                        methods.append(f"{node.name}.{sig}")

        return class_names, methods

    def extract_top_level_functions(self) -> list[str]:
        """
        Extract functions defined directly in tree.body (not inside a class).

        Returns:
            List of signature strings, e.g. ["build_skeleton(repo_path, manifest_path)"]
        """
        functions = []
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._build_signature(node))
        return functions

    def extract(self) -> dict:
        """
        Run all three extraction passes and return combined result.

        Returns:
            Dict with keys:
                imports   — sorted list of import names
                classes   — list of class names
                methods   — list of "ClassName.method(args)" strings
                functions — list of top-level function signatures
        """
        imports = self.extract_imports()
        class_names, methods = self.extract_classes_and_methods()
        functions = self.extract_top_level_functions()

        return {
            "imports":   imports,
            "classes":   class_names,
            "methods":   methods,
            "functions": functions,
        }
```

---

### Change 3 — Add `write_class_list()` and `cleanup_class_list()` functions

**Why:** Standalone module-level functions keep the class focused on
extraction. These handle the debug file lifecycle.

**Location:** Insert after the `SkeletonExtractor` class, before the
`# === Core ===` section.

**BEFORE:**
```python
# =============================================================================
# Core
# =============================================================================

def build_skeleton(
```

**AFTER:**
```python
# =============================================================================
# Class list debug helpers
# =============================================================================

def write_class_list(repo_path: Path, entries: list[dict]) -> None:
    """
    Write class_list.txt to repo root for debugging.

    Each entry is a dict with keys: path, classes, methods.
    File is overwritten on every call.

    Args:
        repo_path: Root path of the target repo.
        entries:   List of per-file dicts collected during build_skeleton().
    """
    out_path = repo_path / CLASS_LIST_PATH
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# class_list.txt — generated by skeleton_reader\n")
        f.write("# Debug output. Safe to delete. Overwritten on next run.\n\n")
        for entry in entries:
            if not entry.get("classes"):
                continue
            f.write(f"{entry['path']}\n")
            for class_name in entry["classes"]:
                f.write(f"  {class_name}\n")
                for method_sig in entry.get("methods", []):
                    if method_sig.startswith(f"{class_name}."):
                        f.write(f"    - {method_sig}\n")
            f.write("\n")


def cleanup_class_list(repo_path: Path) -> None:
    """
    Delete class_list.txt from repo root if it exists.

    Called at the start of build_skeleton() to remove the previous run's
    debug output before the new run begins.

    Args:
        repo_path: Root path of the target repo.
    """
    out_path = repo_path / CLASS_LIST_PATH
    if out_path.exists():
        out_path.unlink()


# =============================================================================
# Core
# =============================================================================

def build_skeleton(
```

---

### Change 4 — Update `build_skeleton()` to use `SkeletonExtractor` and class list

**Why:** Wire up the new class and debug file lifecycle.

**BEFORE** (inside `build_skeleton()`, the try block for Python files):
```python
            try:
                source = file_path.read_text(encoding="utf-8")
                skeleton = _extract_python_skeleton(source)
                entry.update(skeleton)
                stats["python_parsed"] += 1
```

**AFTER:**
```python
            try:
                source = file_path.read_text(encoding="utf-8")
                skeleton = SkeletonExtractor(source).extract()
                entry.update(skeleton)
                stats["python_parsed"] += 1
```

**BEFORE** (top of `build_skeleton()`, just after the manifest is loaded
and `documents` is assigned, before `stats = {`):
```python
    documents = manifest["documents"]

    stats = {
```

**AFTER:**
```python
    documents = manifest["documents"]

    # Clean up previous run's debug output before starting
    cleanup_class_list(repo_path)

    stats = {
```

**BEFORE** (end of `build_skeleton()`, the return statement):
```python
    return {
        "files":     files,
        "stats":     stats,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    }
```

**AFTER:**
```python
    # Write debug class list for this run
    write_class_list(repo_path, files)

    return {
        "files":     files,
        "stats":     stats,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    }
```

---

### Change 5 — Add `class_list.txt` to `.gitignore`

**File:** `.gitignore` (repo root)

Add the following line in an appropriate section (e.g. under debug/temp
outputs):

```
class_list.txt
```

---

### Summary of output dict changes

The dict returned per Python file gains one key and changes one:

| Key | Before | After |
|---|---|---|
| `imports` | list of strings | unchanged |
| `classes` | list of class names | unchanged |
| `functions` | flat list, included methods (unreliably) | top-level functions only |
| `methods` | *(absent)* | `ClassName.method(args)` strings |

Downstream consumers (e.g. `repo_reader.py`) should be checked to see
if they reference the `functions` key and would benefit from also
rendering `methods`.
