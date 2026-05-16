# guided.md

**Path:** experiments/01_readme_gen/prompts/guided.md
**Syntax:** markdown
**Generated:** 2026-05-15 14:53:19

```markdown
You are a technical writer generating a README for a Python package.

The package name is: **{{ package_name }}**

## Repository Structure

The following is a structural outline of the `{{ package_name }}` package
from the dev-utils monorepo. Each entry shows the file path, imports,
classes, and function signatures for Python files, or full content for
small configuration files.

USE ONLY THE INFORMATION PROVIDED BELOW. Do not invent features,
classes, or functions that are not present in this structure. If
information needed for a section is not available, write "TBD".

{{ repo_context }}

## Your Task

Generate a complete README.md for the `{{ package_name }}` package.

Base the README strictly on what you can see in the repository structure
above. Do not invent features or capabilities that are not present in
the imports, classes, or function signatures.

## Style Standard

Model your output on the fletcher README, which is included in the
repository structure above at `python/fletcher/README.md`.

Match its tone, structure, and level of detail. Do not copy its
content — use it as a structural reference only.

## Required Sections

Every README must include the following sections, in this order:

1. **Package name and one-line description** — what it does in plain English
2. **Installation** — standard venv + pip install -e . pattern, cross-platform
3. **Quick Start** — minimal working example to get something running
4. **What It Does** — input, output, and primary use case
5. **Configuration** — any config files, environment variables, or options
6. **Dependencies** — Python version and required packages
7. **Development** — how to clone, install in dev mode, and run tests
8. **Part of Project Crew** — standard ecosystem blurb (see fletcher README)
9. **License** — MIT, refer to LICENSE file

Omit a section only if it genuinely does not apply to this package.
Write "TBD" for sections that apply but lack available information.

## Installation Pattern

Always use this pattern for Installation and Development sections:

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

Do not use absolute paths. Do not reference /opt or any system directories.

## Output Format

Write only the README content — no preamble, no explanation, just the
markdown.

```
