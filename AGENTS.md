# AGENTS Guidelines

- Read definitions and terminology in `DEFNS.md`
- Specifications live in `SPEC.md` files:
  - The **root** `SPEC.md` covers the project as a whole (structure, shared requirements, integration testing).
  - **Subfolder** `SPEC.md` files (e.g. `resources/tok/SPEC.md`) are scoped to that component — they own their own usage, implementation, and test definitions.
  - Subfolder specs inherit project-wide non-functional requirements (e.g. POS style from `DEFNS.md`) unless they explicitly override them.
  - When assessing drift or planning changes, read **all** `SPEC.md` files, not just the root.

- When planning nontrivial changes update the `TODO.md` which sits alongside the relevant `SPEC.md`
- Keep the TODOs up to date
- Pause between TODO items and invite the operator to review

- If asked to make changes ad-hoc (i.e. not part of original specification) ask if you should update `SPEC.md` to match

## Tests
- `test.sh` is the integration test for `bootstrap_inst.sh`/`install.py`. It launches a fresh incus container, runs setup, and verifies all tools, symlinks, and configs. Incus must be initialised on the host.
- Subfolders with their own `SPEC.md` may have local pytest tests (e.g. `resources/tok/test.py`). pytest must be the entry point (it discovers and runs `test_*` functions), so use `uv run --with pytest pytest <path> -v` to supply pytest as an ad-hoc dependency.
