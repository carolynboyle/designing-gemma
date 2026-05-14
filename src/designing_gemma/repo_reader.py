# =============================================================================
# designing_gemma/repo_reader.py
# Reads a manifest.skel file or skeleton data dict and formats its contents
# as a prompt-injectable text block for use as a Jinja2 template variable
# ({{ repo_context }}).
#
# Gemma receives a compact structural outline of the target repo rather than
# raw source files. Token budget is enforced — large repos are truncated
# cleanly at file boundaries, never mid-file.
# =============================================================================

from pathlib import Path

import yaml


DEFAULT_MAX_CHARS = 40_000   # conservative default — adjust per experiment


class RepoReaderError(Exception):
    """Raised when manifest.skel cannot be read or parsed."""


# =============================================================================
# Formatting helpers
# =============================================================================

def _format_python_entry(entry: dict) -> str:
    """Format a Python skeleton entry as a readable text block."""
    lines = [f"=== {entry['path']} ===", "[Python]"]

    imports = entry.get("imports", [])
    if imports:
        lines.append(f"imports: {', '.join(imports)}")
    else:
        lines.append("imports: (none)")

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

    return "\n".join(lines)


def _format_non_python_entry(entry: dict) -> str:
    """Format a non-Python entry as a readable text block."""
    suffix = Path(entry["path"]).suffix.lstrip(".").upper() or "FILE"
    lines  = [f"=== {entry['path']} ==="]

    if entry.get("included"):
        lines.append(f"[{suffix} - full content]")
        lines.append(entry.get("content", ""))
    else:
        reason = entry.get("reason", "excluded")
        lines.append(f"[excluded: {reason}]")

    return "\n".join(lines)


def _format_entry(entry: dict) -> str:
    """Dispatch to correct formatter based on file type."""
    file_type = entry.get("type", "")

    if file_type in ("python", "python_unparseable"):
        return _format_python_entry(entry)

    return _format_non_python_entry(entry)


# =============================================================================
# Core
# =============================================================================

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
                    Truncation happens at file boundaries — never mid-file.

    Returns:
        Dict with keys:
            context_text     — formatted string ready for {{ repo_context }}
            files_included   — count of files included in output
            files_excluded   — count of files excluded due to budget
            total_chars      — character count of context_text
            truncated        — bool, True if budget was reached

    Raises:
        RepoReaderError: If source cannot be read or parsed.
    """
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

    files          = data["files"]
    blocks         = []
    total_chars    = 0
    files_included = 0
    files_excluded = 0
    truncated      = False

    for entry in files:
        block     = _format_entry(entry)
        block_len = len(block) + 2   # +2 for trailing newlines

        if total_chars + block_len > max_chars:
            files_excluded += 1
            truncated       = True
            continue

        blocks.append(block)
        total_chars    += block_len
        files_included += 1

    if truncated:
        note = (
            f"\n[output truncated: {files_excluded} file(s) omitted "
            f"due to {max_chars:,} character limit]"
        )
        blocks.append(note)
        total_chars += len(note)

    context_text = "\n\n".join(blocks)

    return {
        "context_text":   context_text,
        "files_included": files_included,
        "files_excluded": files_excluded,
        "total_chars":    total_chars,
        "truncated":      truncated,
    }
