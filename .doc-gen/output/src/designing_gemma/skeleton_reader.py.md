# skeleton_reader.py

**Path:** src/designing_gemma/skeleton_reader.py
**Syntax:** python
**Generated:** 2026-05-13 22:16:06

```python
# =============================================================================
# designing_gemma/skeleton_reader.py
# Reads a doc-gen manifest.yml, extracts structural summaries from Python
# source files using the ast module, and writes a manifest.skel file.
#
# Non-Python files are included as-is if under the size limit, or flagged
# for exclusion. Gemma never sees raw source files — only the skeleton.
#
# CLI entry point: designing-gemma-skel (see pyproject.toml)
# Run once per repo before experiments that require repo context.
# =============================================================================

import ast
import sys
import datetime
from pathlib import Path

import yaml


# =============================================================================
# Constants
# =============================================================================

# Files and directories to always skip regardless of manifest contents.
# Mirrors doc-gen's HARDCODED_IGNORES pattern.
HARDCODED_SKIP_PATTERNS = [
    ".egg-info",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".doc-gen",
]

DEFAULT_MANIFEST_PATH = ".doc-gen/manifest.yml"
DEFAULT_SKEL_PATH     = ".doc-gen/manifest.skel"
DEFAULT_SIZE_LIMIT    = 5000   # characters — non-Python files above this are excluded


class SkeletonError(Exception):
    """Raised when skeleton extraction fails unrecoverably."""


# =============================================================================
# Helpers
# =============================================================================

def _should_skip(path_str: str) -> bool:
    """Return True if path matches any hardcoded skip pattern."""
    for pattern in HARDCODED_SKIP_PATTERNS:
        if pattern in path_str:
            return True
    return False


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


# =============================================================================
# Core
# =============================================================================

def build_skeleton(
    repo_path: Path,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    size_limit: int = DEFAULT_SIZE_LIMIT,
    size_overrides: list[str] | None = None,
) -> dict:
    """
    Read manifest.yml, extract skeletons, return structured data.

    Args:
        repo_path:      Root path of the target repo.
        manifest_path:  Path to manifest.yml relative to repo_path.
        size_limit:     Max characters for non-Python file inclusion.
        size_overrides: List of file paths (relative to repo root) to
                        include at full size regardless of size_limit.
                        Useful for style reference files like README.md.

    Returns:
        Dict with keys:
            files            — list of per-file skeleton dicts
            stats            — processing statistics
            generated        — ISO timestamp string

    Raises:
        SkeletonError: If manifest.yml cannot be read or parsed.
    """
    manifest_file = repo_path / manifest_path

    if not manifest_file.exists():
        raise SkeletonError(f"manifest.yml not found: {manifest_file}")

    try:
        with manifest_file.open("r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SkeletonError(f"Failed to parse manifest.yml: {e}") from e

    if not isinstance(manifest, dict) or "documents" not in manifest:
        raise SkeletonError("manifest.yml is missing 'documents' key.")

    documents = manifest["documents"]

    stats = {
        "total":               len(documents),
        "python_parsed":       0,
        "python_unparseable":  0,
        "non_python_included": 0,
        "non_python_excluded": 0,
        "skipped_hardcoded":   0,
    }

    overrides = set(size_overrides) if size_overrides else set()
    files = []

    for doc in documents:
        path_str = doc.get("path", "")
        if not path_str:
            continue

        # Skip hardcoded patterns (egg-info, pycache, etc.)
        if _should_skip(path_str):
            stats["skipped_hardcoded"] += 1
            continue

        file_path = repo_path / path_str

        # Python files — ast extraction
        if path_str.endswith(".py"):
            entry = {"path": path_str, "type": "python"}
            if not file_path.exists():
                entry["error"] = "file_not_found"
                files.append(entry)
                continue

            try:
                source = file_path.read_text(encoding="utf-8")
                skeleton = _extract_python_skeleton(source)
                entry.update(skeleton)
                stats["python_parsed"] += 1
            except SyntaxError as e:
                entry["type"]  = "python_unparseable"
                entry["error"] = str(e)
                stats["python_unparseable"] += 1
            except (OSError, UnicodeDecodeError) as e:
                entry["error"] = f"read_error: {e}"

            files.append(entry)

        # Non-Python files — include if under size limit
        else:
            entry = {"path": path_str, "type": "non-python"}
            if not file_path.exists():
                entry["included"] = False
                entry["reason"]   = "file_not_found"
                files.append(entry)
                continue

            try:
                content    = file_path.read_text(encoding="utf-8", errors="replace")
                size_chars = len(content)
                entry["size_chars"] = size_chars

                if size_chars <= size_limit or path_str in overrides:
                    entry["included"] = True
                    entry["content"]  = content
                    stats["non_python_included"] += 1
                else:
                    entry["included"] = False
                    entry["reason"]   = "exceeds_size_limit"
                    stats["non_python_excluded"] += 1

            except OSError as e:
                entry["included"] = False
                entry["reason"]   = f"read_error: {e}"
                stats["non_python_excluded"] += 1

            files.append(entry)

    return {
        "files":     files,
        "stats":     stats,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def write_skel(
    skeleton_data: dict,
    repo_path: Path,
    skel_path: str = DEFAULT_SKEL_PATH,
) -> Path:
    """
    Write skeleton data to manifest.skel.

    Args:
        skeleton_data: Output of build_skeleton().
        repo_path:     Root path of the target repo.
        skel_path:     Output path relative to repo_path.

    Returns:
        Absolute path to the written file.
    """
    out_path = repo_path / skel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Generated by designing-gemma skeleton_reader\n")
        f.write(f"# Source: {DEFAULT_MANIFEST_PATH}\n")
        f.write(f"# Generated: {skeleton_data['generated']}\n\n")
        yaml.dump(
            {"files": skeleton_data["files"]},
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    return out_path.resolve()


# =============================================================================
# CLI entry point
# =============================================================================

def main() -> None:
    """
    CLI entry point: designing-gemma-skel <repo_path> [--override <path>] ...

    Reads manifest.yml from the target repo and writes manifest.skel.
    Diagnostic tool — the runner calls build_skeleton() directly at runtime.

    Options:
        --override <path>   Include file at full size regardless of size limit.
                            May be specified multiple times.

    Example:
        designing-gemma-skel /repos/dev-utils --override python/fletcher/README.md
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="designing-gemma-skel",
        description="Generate manifest.skel from doc-gen manifest.yml",
    )
    parser.add_argument(
        "repo_path",
        help="Path to target repo (must contain .doc-gen/manifest.yml)",
    )
    parser.add_argument(
        "--override",
        action="append",
        dest="size_overrides",
        metavar="PATH",
        default=[],
        help="Include file at full size regardless of size limit (repeatable)",
    )

    args = parser.parse_args()
    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"ERROR: repo path not found: {repo_path}")
        sys.exit(1)

    print(f"Building skeleton for: {repo_path}")
    if args.size_overrides:
        print(f"  Size overrides: {args.size_overrides}")

    try:
        skeleton_data = build_skeleton(
            repo_path,
            size_overrides=args.size_overrides or None,
        )
    except SkeletonError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    stats = skeleton_data["stats"]
    print(f"  Total files in manifest : {stats['total']}")
    print(f"  Python files parsed     : {stats['python_parsed']}")
    print(f"  Python unparseable      : {stats['python_unparseable']}")
    print(f"  Non-Python included     : {stats['non_python_included']}")
    print(f"  Non-Python excluded     : {stats['non_python_excluded']}")
    print(f"  Skipped (hardcoded)     : {stats['skipped_hardcoded']}")

    out_path = write_skel(skeleton_data, repo_path)
    print(f"\n  Written: {out_path}")


if __name__ == "__main__":
    main()

```
