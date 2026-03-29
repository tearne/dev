# Proposal: Host-Based Integration Test
**Status: Approved**

## Intent
The existing integration test (`tests/integration.sh`) requires nested Incus containers, which
is rarely feasible in practice. A host-based alternative can exercise the majority of interesting
installation paths — everything that doesn't need root — without any container infrastructure.

## Specification Deltas

### MODIFIED
- Integration test no longer requires Incus. It runs directly on the host with an isolated `HOME`,
  skipping items that require apt/root. Items requiring apt prerequisites (`rust` and its
  dependents, `pyright`) are skipped if those prerequisites (`build-essential`, `libatomic1`)
  are not already installed on the host.

### ADDED
- The test sets `HOME` to a temporary directory and supplies appropriate env overrides
  (`CARGO_HOME`, `UV_TOOL_DIR`, etc.) so installs do not touch the real user home.
- The test explicitly sets `PATH` to include install destinations (`$CARGO_HOME/bin`,
  `$UV_TOOL_BIN_DIR`, `$HOME/.local/bin`) before running callability assertions, since
  `.profile` is not sourced in the test shell.
- Items skipped in the host test: `htop`, `btop`, `wl-clipboard`, `xclip`, `incus`,
  `unattended-upgrades`, `all-upgrades`, `helix` (requires `dpkg`).
- Items conditionally skipped: `rust`, `rust-analyzer`, `cargo-binstall`, `zellij`, `delta`,
  `difft`, `harper-ls`, `markdown-oxide` (skipped if `build-essential` absent);
  `pyright` (skipped if `libatomic1` absent).
- Items always exercised: `ruff`, `biome`, `tok`, git config, PATH setup, config symlinks.

## Scope
- **In scope**: replacing the Incus-based test with a host-based test. `tests/integration.sh` will be removed.
- **Out of scope**: restoring container-based coverage.

## Limitations

By retiring the container-based test, the following are no longer verified by automated testing:

- **apt/sudo installs**: `htop`, `btop`, `wl-clipboard`, `xclip`, `incus`, `unattended-upgrades`, `all-upgrades`, and `helix` (via `dpkg`) are untested end-to-end.
- **Clean OS baseline**: the host test cannot guarantee a clean starting state; pre-existing tools on the host may mask installation failures.
- **Rust toolchain and dependents**: `rust`, `rust-analyzer`, `cargo-binstall`, `zellij`, `delta`, `difft`, `harper-ls`, `markdown-oxide` are only exercised if `build-essential` is already present on the host.
- **Full PATH and shell config integration**: `.profile` and `.bashrc` are written to a temp directory and never sourced, so shell integration is not exercised end-to-end.
