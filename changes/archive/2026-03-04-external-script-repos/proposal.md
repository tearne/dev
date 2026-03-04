# Proposal: External Script Repositories
**Status: Ready for Review**

## Intent

`tok` is a standalone tool with its own `SPEC.md`, tests, and change history. Keeping it inside
this repository creates unnecessary coupling: changes to `tok` require commits here, and this
installer repo bears responsibility for a tool that has an independent lifecycle.

The goal is to move `tok` into its own repository (`github.com/tearne/tok`) and introduce a
convention that allows scripts in *any* external repository to be installed by this installer,
while ensuring only explicitly approved versions are ever installed.

## Specification Deltas

### ADDED

**External script repositories**

- The installer maintains a registry of approved external scripts; each entry specifies the
  repository, a pinned version, an entrypoint filename, and an optional installed name
  (defaulting to the entrypoint stem); the installer determines the destination directory
- The installer maintains a registry of approved external repositories, each with a pinned
  version; only pinned versions may be installed
- Updating a pinned version is a deliberate, reviewable action in this repository
- If an approved version has already been fetched, installation proceeds without network access
- Externally-sourced items appear in the TUI and respect dependency ordering, but are visually
  distinguished from built-in items (e.g. labelled or annotated to indicate their origin)

**Security**

- The installer verifies that what was fetched matches the approved version before installing
  any files

### MODIFIED

- **`tok` installation**: `tok` is installed from `github.com/tearne/tok` at the pinned version
  recorded in this repository, rather than from `resources/tok/`

### REMOVED

- `resources/tok/` directory and all its contents — `tok.py`, `test.py`, `SPEC.md`, and the
  `changes/` history — migrated to the `tok` repository

## Scope

- **Out of scope**: automatic update checking, installing multiple scripts from a single
  external repository
- **In scope**: the installable-repository convention, the registry, and migration of `tok`
