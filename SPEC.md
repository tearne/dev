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
- After an optional initial password prompt, no further user input is required.
- Prompts for sudo password once at start. Skips the prompt when running as root or when sudo credentials are already cached (passwordless sudo).
- If a tool is already installed, it is skipped.
- On failure, exits immediately. The last log line identifies the failed command and its exit code.
- Each installation step displays the shell command being run, without scrolling previous output off screen.
- Installs its own dependencies at runtime where possible (e.g. `uv`, `curl`).

### Tools Installed
All latest stable versions:
- `uv`
- Rust (`rustc`, `cargo`, `rust-analyzer`)
- Helix editor (`hx`) with language servers: `harper-ls`, `pyright`, `ruff`
- Zellij (`zellij`)
- `htop`, `btop`, `incus`

### Incus
- Incus is initialised (`incus admin init`) with ZFS storage backend.
- Falls back to `dir` backend when ZFS is not installed.

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
- Python 3.12, `uv` as runtime.
- No flags or configuration — to customise, edit `install.py` directly.
- `uv` bootstrapped via `curl`.
- Rust installed via RustUp (via `curl`).
- Helix installed from latest stable `.deb` on GitHub releases.
- `harper-ls` and Zellij installed via `cargo binstall`.
- `pyright` and `ruff` installed via `uv`.
- `htop`, `btop`, `incus` installed non-interactively via apt (no PPA).
- Root structure:
```
<project root>/
├── resources/  # Config files to be soft linked during installation
├── bootstrap_inst.sh  # Bash entry point, bootstraps uv
├── install.py         # Python logic (uv single-file script)
├── test.sh     # Incus test harness
```

## Verification

- Tests run within an `incus` container (latest LTS Ubuntu).
- Test where possible but avoid disproportionate complexity or polluting external API.

### Test Scenarios
- Installation completes without error.
- Each tool is callable: `htop`, `btop`, `incus`, `rustc`, `cargo`, `zellij`, `hx`, `harper-ls`, `pyright`, `ruff`.
- Config symlinks point to the expected relative targets.
- Config file content matches spec (e.g. `theme = "autumn"`, `dialect = "British"`).
- New terminals have `~/.local/bin` on `PATH`.
- Existing configs are not overwritten; warnings are shown at end.

### Not Tested
- Sudo password prompt behaviour (requires interactive terminal).
- Incus ZFS vs dir fallback (depends on host storage setup).
