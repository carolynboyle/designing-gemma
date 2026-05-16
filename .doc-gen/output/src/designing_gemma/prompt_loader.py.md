# prompt_loader.py

**Path:** src/designing_gemma/prompt_loader.py
**Syntax:** python
**Generated:** 2026-05-15 14:53:19

```python
# =============================================================================
# designing_gemma/prompt_loader.py
# Loads prompt .md files and renders Jinja2 templates.
# Variable injection depends on the experiment — callers provide the context.
# =============================================================================

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


class PromptError(Exception):
    """Raised when a prompt file is missing or fails to render."""


def load_prompt(
    prompt_file: str,
    prompt_dir: str | Path,
    context: dict | None = None,
) -> str:
    """
    Load a Jinja2 prompt template and render it with the given context.

    Args:
        prompt_file:  Filename of the prompt (e.g. 'guided.md')
        prompt_dir:   Directory containing prompt files
        context:      Dict of variables to inject into the template.
                      If None, renders with no variables.

    Returns:
        Rendered prompt string.

    Raises:
        PromptError: If the file is not found or rendering fails due to
                     an undefined variable (StrictUndefined enforced).
    """
    prompt_dir = Path(prompt_dir)
    context = context or {}

    if not prompt_dir.exists():
        raise PromptError(f"Prompt directory not found: {prompt_dir}")

    env = Environment(
        loader=FileSystemLoader(str(prompt_dir)),
        undefined=StrictUndefined,      # fail loudly on missing variables
        keep_trailing_newline=True,
    )

    try:
        template = env.get_template(prompt_file)
    except TemplateNotFound as e:
        raise PromptError(
            f"Prompt file not found: {prompt_dir / prompt_file}"
        ) from e

    try:
        rendered = template.render(**context)
    except Exception as e:
        raise PromptError(
            f"Failed to render {prompt_file}: {e}"
        ) from e

    return rendered


def load_corpus(source: str, source_type: str) -> str:
    """
    Load corpus text from a file or URL.

    Args:
        source:       File path or URL string
        source_type:  'file' or 'url'

    Returns:
        Corpus text as a string.

    Raises:
        PromptError: If the file is not found or the URL fetch fails.
        ValueError:  If source_type is not 'file' or 'url'.
    """
    if source_type == "file":
        path = Path(source)
        if not path.exists():
            raise PromptError(f"Corpus file not found: {path}")
        return path.read_text(encoding="utf-8")

    if source_type == "url":
        import requests  # local import — only needed for url corpora
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise PromptError(f"Failed to fetch corpus from {source}: {e}") from e

    raise ValueError(f"Unknown source_type: {source_type!r}. Must be 'file' or 'url'.")

```
