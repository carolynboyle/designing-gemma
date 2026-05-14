You are a technical writer reviewing a Python monorepo called dev-utils.

## Repository Structure

The following is a structural outline of the dev-utils repository.
Each entry shows the file path, imports, classes, and function signatures
for Python files, or full content for small configuration files.

{{ repo_context }}

## Your Task

### Step 1: Inventory

From the repository structure above, identify all Python packages.
A Python package is any subdirectory under `python/` that contains a
`pyproject.toml` file.

For each package, report one of the following:
- HAS README — a README.md exists and has content
- EMPTY README — a README.md exists but is empty or nearly empty
- MISSING README — no README.md exists

Output the inventory as a simple list, one package per line,
in alphabetical order:

  packagename: HAS README / EMPTY README / MISSING README

### Step 2: Generate

From the packages marked EMPTY README or MISSING README, identify the
first one alphabetically. Generate a complete README.md for that package.

Base the README on what you can see in the repository structure above —
imports, class names, and function signatures tell you what the package
does. Do not invent features or capabilities that are not present.

The README should be useful to a developer who wants to install and use
the package. Use your judgment about what sections are appropriate.

Write only the README content — no preamble, no explanation, just the
markdown.
