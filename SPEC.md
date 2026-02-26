# Specification: Dev Environment Setup CLI

## Overview

This project contains items to help set up a development environment on Ubuntu/Debian
- a script to install basic dev tools
- config files to install
- helper scripts (e.g. a tool to hold encrypted tokens)

## Usage

- Run one command sets everything up:
  - `bootstrap_inst.sh` if system doesn't have `uv` installed already
  - otherwise `install.py` can be used directly.

## Behaviour

### Installation Process
- Before installation begins, a full-screen interactive menu is presented listing all installable items, all selected by default. The user may deselect items before confirming with Enter.
- Passing `--all`, `--only <item> [...]`, or `--skip <item> [...]` bypasses the menu for non-interactive use. Items may be specified by full id or short name. If no flag is given and stdin is not a TTY, the script exits with an error directing the user to rerun with one of the three flags.
- `-l`/`--list` prints a plain-text table of all installable items (id, short name, description) and exits without installing anything.
- Prompts for sudo password once at start. Skips the prompt when running as root or when sudo credentials are already cached (passwordless sudo).
- If a tool is already installed, it is skipped.
- On failure, exits immediately. The last log line identifies the failed command and its exit code.
- Each installation step displays the shell command being run, without scrolling previous output off screen.
- Installs its own dependencies at runtime where possible (e.g. `uv`, `curl`).

### Tools Installed
All latest stable versions. The following are the default (all-selected) items; each can be individually included or excluded via the menu or CLI flags:
- `htop`, `btop`, `incus`, `unattended-upgrades` (`upgrades`) — unattended-upgrades updates all apt repos, not security-only
- Rust (`rustc`, `cargo`, `rust-analyzer`) — prerequisite for `zellij` and `harper-ls`
- Zellij (`zellij`)
- Helix editor (`hx`), with LSPs as a nested group:
  - `harper-ls` (short name: `harper`)
  - `pyright`
  - `ruff`
- `tok`

`uv` is always installed (it bootstraps the script itself) and is not a selectable item.

Item interdependencies:
- Selecting `zellij` or `harper-ls` auto-selects `rust`; deselecting both auto-deselects `rust` unless it was independently selected.

### Incus
- Incus is initialised (`incus admin init`) with ZFS storage backend.
- Falls back to `dir` backend when ZFS is not installed.
- The already-initialised check runs with sudo, so it works correctly for users not in the `incus-admin` group.

### Scripts
- `tok` installed in `~/.local/bin/` (see `resources/tok/SPEC.md`)

### Configuration
- `~/.local/bin/` is on the user's `PATH` in new terminals.
- Config files are symlinked (relative paths) from the resources folder, so the project can be checked out anywhere.
- Dangling symlinks are replaced silently.
- Existing config files are never overwritten. If the installable config differs (ignoring whitespace), a warning is recorded and displayed at the end of the run with a diff.
- Helix config includes:
  - `true-color` enabled
  - `autumn` theme
  - Ruler at column 80
  - Relative line numbers
  - Bufferline always shown
  - Soft-wrap for markdown files
  - `harper-ls` configured with British English dictionary
  - Language server config for installed LSPs

### Logging
- Structured/hierarchical log output showing current stage/sub-stage and process output.
- An install log file records all commands and their full output. Overwritten on each run.

## Constraints

- POS style (see `DEFINITIONS.md`).
- Python 3.12, `uv` as runtime. `textual` as approved third-party dependency (TUI).
- `uv` bootstrapped via `curl`.
- Rust installed via RustUp (via `curl`). Requires `build-essential` (apt) as a prerequisite for the C linker and standard library headers.
- Helix installed from latest stable `.deb` on GitHub releases.
- `harper-ls` and Zellij installed via `cargo binstall`.
- `pyright` and `ruff` installed via `uv`. `pyright` additionally requires `libatomic1` (apt) as a runtime dependency of the Node.js binary it downloads.
- `htop`, `btop`, `incus`, `unattended-upgrades` installed non-interactively via apt (no PPA).
- Root structure:
```
<project root>/
├── resources/  # Config files to be soft linked during installation
├── tests/
│   ├── unit.py          # Unit tests (no container required)
│   └── integration.sh   # Incus integration test harness
├── bootstrap_inst.sh  # Bash entry point, bootstraps uv
├── install.py         # Python logic (uv single-file script)
```

## Verification

Two test layers:

- **Unit tests** (`tests/unit.py`) — cover file-operation logic (symlink creation, config diffing, PATH setup). Run with `uv run --with pytest pytest tests/unit.py`. No container required.
- **Integration tests** (`tests/integration.sh`) — run the full install inside an Incus container (latest LTS Ubuntu). Requires Incus on the host. Test where possible but avoid disproportionate complexity or polluting external API.

### Unit Test Scenarios (`tests/unit.py`)
- Config diff:
  - Files with equivalent content (ignoring whitespace) are treated as identical.
  - Files with differing content produce a unified diff.
- Helix config symlinks:
  - Created with correct relative targets.
  - Existing correct symlink is skipped without warning.
  - Dangling symlink is replaced silently.
  - Real file with different content is not overwritten; a warning is issued.
  - Real file with whitespace-equivalent content is skipped without warning.
- PATH setup:
  - `~/.local/bin` export is appended to `.profile` when not present.
  - Not appended again if already present.
- Selection resolution:
  - Selecting an item with a prerequisite auto-selects the prerequisite.
  - Deselecting an item removes its auto-selected prerequisite when no other selected item needs it.
  - A prerequisite independently selected by the user is retained when dependent items are deselected.
  - `--only` and `--skip` flag subsets are resolved correctly.
- Item short names:
  - `short_name` defaults to `id` when not explicitly set.
  - `--only`/`--skip` accept both full id and short name.
  - Unknown names are rejected with an error.
  - `--list` output contains id, short name, and description.

### Integration Test Scenarios (`tests/integration.sh`)
- Tool installation:
  - Installation completes without error.
  - Each tool is callable: `htop`, `btop`, `incus`, `rustc`, `cargo`, `zellij`, `hx`, `harper-ls`, `pyright`, `ruff`.
  - `rustc` compiles and links a minimal program successfully (verifying `build-essential` is present, not just that the toolchain is on PATH).
  - `pyright --version` executes successfully (verifying the Node.js runtime loads, not just that the wrapper script is on PATH).
- Symlinks:
  - Helix config symlinks point to the expected relative targets.
  - `tok` symlink points to the expected relative target.
- Config content matches spec (`theme = "autumn"`, `dialect = "British"`).
- New terminals have `~/.local/bin` on `PATH`.
- Existing config is not overwritten on re-run; warning is emitted.
- `install.log` exists after a run and contains no ANSI escape sequences.

### Not Tested
- Sudo password prompt behaviour (requires interactive terminal).
- Incus ZFS vs dir fallback (depends on host storage setup).
- `unattended-upgrades` configuration (requires apt and systemd).
