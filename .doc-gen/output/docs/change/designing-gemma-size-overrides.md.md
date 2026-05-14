# designing-gemma-size-overrides.md

**Path:** docs/change/designing-gemma-size-overrides.md
**Syntax:** markdown
**Generated:** 2026-05-13 22:16:06

```markdown
# Changeset: size_overrides for skeleton_reader
## designing-gemma

Adds a `size_overrides` parameter to `build_skeleton()` so specific files
can be included at full size regardless of the size limit. Experiment configs
declare which files they need at full size. The runner passes them through
to `build_skeleton()` at run time. The CLI gains `--override` flags for
diagnostic use.

---

## 1. src/designing_gemma/skeleton_reader.py

### Change 1a: build_skeleton() signature

**BEFORE:**
```python
def build_skeleton(
    repo_path: Path,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    size_limit: int = DEFAULT_SIZE_LIMIT,
) -> dict:
    """
    Read manifest.yml, extract skeletons, return structured data.

    Args:
        repo_path:     Root path of the target repo.
        manifest_path: Path to manifest.yml relative to repo_path.
        size_limit:    Max characters for non-Python file inclusion.
```

**AFTER:**
```python
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
```

**Why:** Allows per-experiment control over which files bypass the size
limit without raising the global limit for all files.

---

### Change 1b: size_overrides local variable

Add immediately after the `stats = {...}` block inside `build_skeleton()`:

**BEFORE:**
```python
    files = []

    for doc in documents:
```

**AFTER:**
```python
    overrides = set(size_overrides) if size_overrides else set()
    files = []

    for doc in documents:
```

**Why:** Convert to a set once for O(1) lookup per file rather than
scanning the list on every iteration.

---

### Change 1c: size check in non-Python handler

**BEFORE:**
```python
                if size_chars <= size_limit:
                    entry["included"] = True
                    entry["content"]  = content
                    stats["non_python_included"] += 1
                else:
                    entry["included"] = False
                    entry["reason"]   = "exceeds_size_limit"
                    stats["non_python_excluded"] += 1
```

**AFTER:**
```python
                if size_chars <= size_limit or path_str in overrides:
                    entry["included"] = True
                    entry["content"]  = content
                    stats["non_python_included"] += 1
                else:
                    entry["included"] = False
                    entry["reason"]   = "exceeds_size_limit"
                    stats["non_python_excluded"] += 1
```

**Why:** Files in the overrides set bypass the size check and are always
included at full content.

---

### Change 1d: CLI main() — add --override flag

**BEFORE:**
```python
def main() -> None:
    """
    CLI entry point: designing-gemma-skel <repo_path>

    Reads manifest.yml from the target repo and writes manifest.skel.
    Run once per repo before experiments that require repo context.
    """
    if len(sys.argv) < 2:
        print("Usage: designing-gemma-skel <repo_path>")
        print("  repo_path: path to target repo (must contain .doc-gen/manifest.yml)")
        sys.exit(1)

    repo_path = Path(sys.argv[1]).resolve()

    if not repo_path.exists():
        print(f"ERROR: repo path not found: {repo_path}")
        sys.exit(1)

    print(f"Building skeleton for: {repo_path}")

    try:
        skeleton_data = build_skeleton(repo_path)
    except SkeletonError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
```

**AFTER:**
```python
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
```

**Why:** Replaces manual `sys.argv` parsing with `argparse` to support
the `--override` flag cleanly. Consistent with standard Python CLI
conventions.

---

## 2. src/designing_gemma/experiment_runner.py

**BEFORE:**
```python
    # Load repo context if experiment specifies repo_read
    repo_read = config.get("repo_read")
    if repo_read:
        from designing_gemma.repo_reader import read_repo_context, RepoReaderError
        repo_key   = repo_read.get("repo")
        skel_path  = Path(repos.get(repo_key, "")) / repo_read.get("manifest", ".doc-gen/manifest.skel")
        max_chars  = repo_read.get("max_chars", 40_000)
        try:
            result = read_repo_context(skel_path, max_chars)
            base_context["repo_context"] = result["context_text"]
            if result["truncated"]:
                print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
        except RepoReaderError as e:
            print(f"  ERROR loading repo context: {e}")
```

**AFTER:**
```python
    # Load repo context if experiment specifies repo_read
    repo_read = config.get("repo_read")
    if repo_read:
        from designing_gemma.repo_reader import read_repo_context, RepoReaderError
        from designing_gemma.skeleton_reader import build_skeleton, SkeletonError
        repo_key       = repo_read.get("repo")
        repo_root      = Path(repos.get(repo_key, ""))
        max_chars      = repo_read.get("max_chars", 40_000)
        size_overrides = repo_read.get("size_overrides") or None
        try:
            skeleton_data = build_skeleton(
                repo_root,
                size_overrides=size_overrides,
            )
            result = read_repo_context(skeleton_data, max_chars)
            base_context["repo_context"] = result["context_text"]
            if result["truncated"]:
                print(f"  WARNING: repo context truncated — {result['files_excluded']} file(s) omitted")
        except (SkeletonError, RepoReaderError) as e:
            print(f"  ERROR loading repo context: {e}")
```

**Why:** Runner now calls `build_skeleton()` directly with per-experiment
`size_overrides` from config. No intermediate `manifest.skel` file required
at run time.

---

## 3. src/designing_gemma/repo_reader.py

`read_repo_context()` needs to accept either a file path or a skeleton
data dict directly, since the runner no longer writes `manifest.skel`
as an intermediary.

**BEFORE:**
```python
def read_repo_context(
    skel_path: str | Path,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict:
    """
    Read manifest.skel and format contents for prompt injection.

    Args:
        skel_path:  Path to manifest.skel file.
        max_chars:  Maximum total characters in the output block.
    ...

    skel_path = Path(skel_path)

    if not skel_path.exists():
        raise RepoReaderError(
            f"manifest.skel not found: {skel_path}\n"
            f"Run skeleton_reader against this repo first:\n"
            f"  designing-gemma-skel {skel_path.parent.parent}"
        )

    try:
        with skel_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RepoReaderError(f"Failed to parse manifest.skel: {e}") from e

    if not isinstance(data, dict) or "files" not in data:
        raise RepoReaderError("manifest.skel is missing 'files' key.")
```

**AFTER:**
```python
def read_repo_context(
    source: str | Path | dict,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict:
    """
    Format skeleton data for prompt injection.

    Args:
        source:     Either a path to manifest.skel (str or Path) or a
                    skeleton data dict as returned by build_skeleton().
        max_chars:  Maximum total characters in the output block.
    ...

    # Accept either a skeleton data dict or a path to manifest.skel
    if isinstance(source, dict):
        data = source
    else:
        skel_path = Path(source)
        if not skel_path.exists():
            raise RepoReaderError(
                f"manifest.skel not found: {skel_path}\n"
                f"Run skeleton_reader against this repo first:\n"
                f"  designing-gemma-skel {skel_path.parent.parent}"
            )
        try:
            with skel_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RepoReaderError(f"Failed to parse manifest.skel: {e}") from e

    if not isinstance(data, dict) or "files" not in data:
        raise RepoReaderError("manifest.skel is missing 'files' key.")
```

**Why:** Allows the runner to pass skeleton data directly without writing
an intermediate file. The file-path code path is preserved so the CLI
diagnostic tool still works.

---

## 4. experiments/01_readme_gen/config.yaml

**BEFORE:** (end of file)
```yaml
    - file: guided.md
      label: guided
      description: >
        Explicit package definitions, required README sections, and style
        standard provided. Tests instruction-following and output quality
        when given a complete spec.
```

**AFTER:**
```yaml
    - file: guided.md
      label: guided
      description: >
        Explicit package definitions, required README sections, and style
        standard provided. Tests instruction-following and output quality
        when given a complete spec.

repo_read:
  repo: dev_utils
  max_chars: 40000
  size_overrides:
    - python/fletcher/README.md
```

**Why:** Injects repo skeleton as `{{ repo_context }}`. The fletcher README
is included at full size as the style reference for the guided prompt.

---

## 5. data/experiment_base.yaml

Add documentation comment after the `repos` block:

**BEFORE:**
```yaml
repos:
  dev_utils: /repos/dev-utils
  sr_barbara: /repos/sr-barbara
```

**AFTER:**
```yaml
repos:
  dev_utils: /repos/dev-utils
  sr_barbara: /repos/sr-barbara

# =============================================================================
# repo_read
# Optional. If present, the runner generates a skeleton of the target repo
# and injects it into every prompt as {{ repo_context }}.
# repo:           key from repos block above
# max_chars:      character budget for injected context (default: 40000)
# size_overrides: list of file paths to include at full size regardless
#                 of the size limit. Paths relative to repo root.
# =============================================================================

# repo_read:
#   repo: dev_utils
#   max_chars: 40000
#   size_overrides:
#     - python/fletcher/README.md
```

---

## After Applying

1. Run `pytest` — verify all tests still pass
2. Rebuild container: `podman-compose build`
3. Run `doc-gen` in dev-utils repo to ensure `manifest.yml` is current
4. Run experiment 01 — runner generates skeleton at runtime, no separate
   `designing-gemma-skel` step needed
5. Verify `{{ repo_context }}` is populated and Gemma produces accurate
   inventory and README output

```
