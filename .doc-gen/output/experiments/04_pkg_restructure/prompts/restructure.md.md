# restructure.md

**Path:** experiments/04_pkg_restructure/prompts/restructure.md
**Syntax:** markdown
**Generated:** 2026-05-13 07:45:45

```markdown
# Package Restructure Task

You are converting a Python package from flat layout to src layout in the dev-utils repository.

## Context

The dev-utils repository has a setupkit registry that expects all packages to use src layout:
```yaml
path_prefix → {path}/src/{name}/
```

Some packages still use flat layout (package code at the root of the package directory). Your task is to convert one package at a time from flat to src layout.

## Layout Definitions

**Flat layout** — package code lives at the package root:
```
python/dbkit/
  pyproject.toml
  dbkit/
    __init__.py
    connection.py
    ...
  tests/
    test_connection.py
    ...
  docs/
    ...
```

**Src layout** — package code lives under a src/ subdirectory:
```
python/dbkit/
  pyproject.toml
  src/
    dbkit/
      __init__.py
      connection.py
      ...
  tests/
    test_connection.py
    ...
  docs/
    ...
```

## Your Task

Convert the provided flat-layout package to src layout. Do this once, completely, for one package only. Then stop.

## Sequencing

1. **Identify the package folder** — the named directory containing `__init__.py` (e.g., `dbkit/` inside `python/dbkit/`)
2. **Create src/ directory** at the package root
3. **Move the entire package folder** into src/
4. **Update pyproject.toml** to declare src layout in `[tool.setuptools.packages.find]`
5. **Run tests** to verify the package still works
6. **Stop and wait** for human verification before doing another package

## What to Change in pyproject.toml

Add or update the `[tool.setuptools.packages.find]` section:

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["{package_name}*"]
```

Where `{package_name}` is the name of the package folder (e.g., `dbkit`, `fletcher`, `viewkit`).

## Important Rules

1. **Do not** delete or move `pyproject.toml`, `README.md`, `tests/`, `docs/`, or any configuration files at the package root — they stay where they are
2. **Move only** the package folder itself (the one with `__init__.py`)
3. **Update only** the `[tool.setuptools.packages.find]` section — do not make other changes to pyproject.toml
4. **After moving**, egg-info directories like `{package_name}.egg-info/` will be stale and should be noted for manual cleanup (human will delete them)
5. **Run tests** after moving to verify imports still work
6. **Stop after one package** — do not attempt to convert multiple packages in a single run

## Output

After completing the restructure:

1. Show the git-style diff or before/after structure
2. Report which files were moved
3. Show the updated pyproject.toml `[tool.setuptools.packages.find]` section
4. Report the test run results
5. End with: **"STOP HERE. Human must verify structure and run `pip install -e .` before proceeding to the next package."**

## Package Information

**Package to restructure:** {{ package_name }}
**Package root:** {{ package_root }}
**Flat package folder:** {{ flat_package_folder }}

Current flat structure at {{ package_root }}:
{{ flat_structure }}

Current pyproject.toml (relevant sections):
{{ current_pyproject }}

```
