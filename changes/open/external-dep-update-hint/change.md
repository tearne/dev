# External Dependency Update Hint
**Type**: Proposal
**Status**: Approved

## Intent

External scripts are pinned to a specific git SHA in `external_scripts.toml`. The installer has no way to tell the user whether a newer commit exists at the remote HEAD. This change adds a visual hint in the menu when an installed external dependency is behind the remote HEAD, so the user knows to consider updating the pinned SHA.

## Specification Deltas

### ADDED

- When the menu loads, each external dependency is checked against its remote HEAD asynchronously (one background thread per dependency).
- While a check is in progress, the item's label shows `[ext ⠋]` with a braille spinner (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏).
- Once the check resolves, the `[ext]` label is replaced by a combined indicator in grey text with a coloured symbol:
  - SHA matches remote HEAD: `[ext a1b2c3 HEAD ✓]` (green tick)
  - SHA is behind remote HEAD: `[ext a1b2c3 update available ?]` (yellow question mark)
  - Check failed (no connectivity, repo unavailable): `[ext ?]`
- In all cases the SHA shown is the pinned SHA (first 7 characters).
- Checks run concurrently; each item's display updates independently as its result arrives.
- TEST: An external dependency is considered installed only when the binary in use resolves to the pinned SHA. A SHA change in `external_scripts.toml` is sufficient to cause the item to be selected for reinstall.
- TEST: The remote HEAD check compares the pinned SHA (from `external_scripts.toml`) against the remote, not the currently installed version. Updating the TOML to a newer SHA will therefore immediately show an outdated indicator until the installer is run.
