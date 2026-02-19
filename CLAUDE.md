# Guidelines

## Definitions
@DEFINITIONS.md

## Tests
- `test.sh` is the integration test for `bootstrap_inst.sh`/`install.py`. It launches a fresh incus container, runs setup, and verifies all tools, symlinks, and configs. Incus must be initialised on the host.
