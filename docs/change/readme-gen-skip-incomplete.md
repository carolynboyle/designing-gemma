# Changeset: Skip Incomplete Packages in readme_gen
## designing-gemma

Adds a pre-render check that detects incomplete packages before calling
the model. A package is considered incomplete if any of its `.py` files
have no imports, no classes, and no functions — the signature of an
empty stub file as produced by treekit.

This replaces the prompt-level instruction ("if any .py file is 0kb,
skip") which both models ignored. The decision is now made in Python
before the model is ever called.

Result files for skipped packages contain only:
`# SKIPPED: {package_name} — package incomplete`

This gives the run log a clean, searchable signal and preserves the
result file for reference.

---

## 1. experiment_runner.py — add _package_has_empty_py_files()

**File path:** `src/designing_gemma/experiment_runner.py`

Add this function after `_filter_skeleton_for_package()` and before
`_run_experiment()`:

**BEFORE:** (no such function exists)

**AFTER:**
```python
def _package_has_empty_py_files(skeleton_data: dict, package_name: str) -> bool:
    """
    Return True if any .py file in the package has no imports, classes,
    or functions — the signature of an empty stub file.

    Used to skip incomplete packages in per-package experiments rather
    than passing empty context to the model and getting hallucinated output.

    Args:
        skeleton_data: Output of build_skeleton().
        package_name:  Package directory name, e.g. "contactkit".

    Returns:
        True if any empty .py file is found in the package.
    """
    prefix = f"python/{package_name}/"
    for entry in skeleton_data.get("files", []):
        if not entry.get("path", "").startswith(prefix):
            continue
        if entry.get("type") != "python":
            continue
        if (
            not entry.get("imports")
            and not entry.get("classes")
            and not entry.get("functions")
        ):
            return True
    return False
```

**Why:** Empty stub files produce a skeleton entry with all four lists
empty. This is unambiguous — a real Python file always has at least one
import or one function. Checking in the runner removes the decision from
the model entirely.

---

## 2. experiment_runner.py — add skip check before prompt loop

**File path:** `src/designing_gemma/experiment_runner.py`

Find the per-package loop where `package_name` is iterated. The check
goes after the per-package skeleton is filtered and before the prompt
loop begins.

**BEFORE:**
```python
                if package_name:
                    pkg_skeleton = _filter_skeleton_for_package(skeleton_data, package_name)
                else:
                    pkg_skeleton = skeleton_data

                result = read_repo_context(pkg_skeleton, max_chars)
                base_context["repo_context"] = result["context_text"]
```

**AFTER:**
```python
                if package_name:
                    pkg_skeleton = _filter_skeleton_for_package(skeleton_data, package_name)

                    # Skip incomplete packages — empty .py stubs produce
                    # hallucinated READMEs that describe unbuilt features.
                    if _package_has_empty_py_files(pkg_skeleton, package_name):
                        skip_msg = f"# SKIPPED: {package_name} — package incomplete"
                        print(f"\n  {skip_msg}")
                        run_id = _run_id(results_dir)
                        for prompt_def in prompts:
                            for model_def in models:
                                out_filename = _output_filename(
                                    run_id,
                                    model_def.get("name"),
                                    prompt_def.get("label", prompt_def.get("file")),
                                    package_name=package_name,
                                )
                                _write_output(results_dir, out_filename, skip_msg)
                        continue
                else:
                    pkg_skeleton = skeleton_data

                result = read_repo_context(pkg_skeleton, max_chars)
                base_context["repo_context"] = result["context_text"]
```

**Why:** Writes a skip marker file for every prompt/model combination
so the run log has a complete record. Uses `continue` to move to the
next package without calling the model at all.

---

## After applying

1. Apply both changes to `experiment_runner.py`
2. Rebuild container: `podman-compose build`
3. Run experiment 01 — verify contactkit, mcpkit, and any other
   incomplete packages produce SKIPPED result files instead of
   hallucinated READMEs
4. Verify complete packages (fletcher, dbkit, setupkit) still
   produce normal output

## Commit message

```
feat: skip incomplete packages in readme_gen — empty .py stubs trigger hallucination
```
