# Proposal: Integration Test Value
**Status: Note**

The integration test (`tests/integration.sh`) requires nested containers (Incus inside Incus),
which is rarely feasible in practice. As a result it is unlikely to be run regularly.

Worth considering: what coverage would be lost if it were dropped, and whether that coverage
could be recovered another way or simply accepted as manual-only.

Coverage the integration test provides that unit tests do not:
- Full install completes without error in a clean Ubuntu environment
- Each tool is actually callable after install (not just that the installer ran)
- `pyright --version` loads the Node.js runtime (not just that the wrapper script exists)
- `rustc` links a real binary (verifying `build-essential`, not just PATH)
- Config symlinks point to the correct relative targets on a real filesystem
- `~/.local/bin` appears on PATH in a new login shell (`.profile` is sourced)
- Existing configs are not overwritten on a re-run; warning is emitted
- `install.log` is written and contains no ANSI escape sequences
- External script fetch and symlink work against a real remote (tok)
