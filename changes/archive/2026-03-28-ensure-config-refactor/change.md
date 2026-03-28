# Ensure Config Refactor
**Type**: Fix
**Status**: Approved

## Log

Add an optional `configure` callback to `InstallItem`. After the install loop, run `configure()` for any item whose install check passes, regardless of what was selected. This replaces the ad-hoc setup function calls at the bottom of `install()` and makes per-tool configuration a first-class concept co-located with the item definition.

### Guarded appends

`append_to_shell_configs` gains an optional `conflict` parameter — a substring to search for in each target file. If a line containing `conflict` is found, that file is skipped entirely, leaving the user's existing configuration untouched.

This distinguishes two cases:

- **Our line is already present** — idempotency, skip silently (existing behaviour)
- **A conflicting line is present** — user has configured this themselves, skip silently (new behaviour)

Example — setting `EDITOR`:

```python
append_to_shell_configs("export EDITOR=hx", conflict="EDITOR=")
```

If `.bashrc` contains `export EDITOR=vim`, the conflict pattern `EDITOR=` matches, so we leave that file alone. If `.bashrc` has no `EDITOR=` at all, we append our line. If `.bashrc` already contains `export EDITOR=hx` exactly, the existing idempotency check catches it first.

PATH is additive so needs no conflict guard — prepending `.local/bin` is always safe regardless of what else is on PATH.
