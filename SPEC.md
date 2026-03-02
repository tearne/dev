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
- Passing `--all`, `--only <item> [...]`, or `--skip <item> [...]` bypasses the menu for non-interactive use. Items are specified by full id. If no flag is given and stdin is not a TTY, the script exits with an error directing the user to rerun with one of the three flags.
- `-l`/`--list` prints a plain-text table of all installable item ids and exits without installing anything.
- Prompts for sudo password once at start. Skips the prompt when running as root or when sudo credentials are already cached (passwordless sudo).
- If a tool is already installed, its installation step is skipped. Idempotent configuration (e.g. git aliases) is applied unconditionally so it is correct on re-runs.
- On failure, exits immediately. The last log line identifies the failed command and its exit code.
- Each installation step displays the shell command being run, without scrolling previous output off screen.
- Installs its own dependencies at runtime where possible (e.g. `uv`, `curl`).

### Tools Installed
All latest stable versions. Items are organised into a visual tree in the TUI. Each item can be individually included or excluded via the menu or CLI flags; all are selected by default.

```
[System]
  [Resource]
    htop, btop
  unattended-upgrades
    all-upgrades — extends automatic updates to all apt repositories (not just security)
  incus, tok, zellij
[Rust]
  rust (rustup/rustc/cargo)
    rust-analyzer
    cargo-binstall
[Git]
  delta (git-delta) — syntax-highlighted git diff pager; exposes git dd and git dl aliases
  difft (difftastic) — structural diff tool; exposes git dft alias
[Helix]
  helix (hx)
    biome — JSON language server
    harper-ls
    markdown-oxide — Markdown language server (replaces marksman)
    pyright
    ruff
```

`uv` is always installed (it bootstraps the script itself) and is not a selectable item.

Item interdependencies:
- Items and groups form a tree. `InstallItem` has a `parent` field (group name or item id) for visual nesting; `Group` likewise. `InstallItem` has no description field; items are identified by id only.
- Toggling any node (group header or item) in the TUI recursively mirrors state to all descendants. Toggling a node on ensures all ancestors are also selected. Group headers are displayed as `[Name]`.
- Install-order dependencies are declared via `requires` on `InstallItem`. `parent` is visual-only and does not imply an install dependency.
- `requires` links are resolved at confirmation time (Enter): if items were added to satisfy dependencies, an apt-style summary is shown and the user is prompted to confirm before installation begins.
- For non-interactive invocations (`--all`/`--only`/`--skip`), auto-resolved dependencies emit a warning to stdout and the log.
- `zellij`, `delta`, `difft`, `harper-ls`, and `markdown-oxide` require `cargo-binstall`; `rust-analyzer` and `cargo-binstall` require `rust`; `all-upgrades` requires `unattended-upgrades`.

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
  - `biome` configured as the language server for JSON files

### Logging
- Structured/hierarchical log output showing current stage/sub-stage and process output.
- An install log file records all commands and their full output. Overwritten on each run.

## Constraints

- POS style (see `DEFINITIONS.md`). Python 3.12, `uv` as runtime; `uv`
  bootstrapped via `curl`. Approved third-party dependencies: `textual`, `rich`.
- Installation method by tool:
  - **apt** (non-interactive, no PPA): `htop`, `btop`, `incus`,
    `unattended-upgrades`; `libatomic1` (pyright runtime dep);
    `build-essential` (rust build dep)
  - **RustUp** (via `curl`): `rust`
  - **`rustup component add`**: `rust-analyzer`
  - **`cargo binstall`**: `cargo-binstall`, `zellij` (`zellij`), `delta`
    (`git-delta`), `difft` (`difftastic`), `harper-ls`; `markdown-oxide` uses
    `--git` (not on crates.io)
  - **GitHub releases**: `helix` (latest stable `.deb`); `biome`
    (arch-appropriate binary → `~/.local/bin/`)
  - **`uv tool install`**: `pyright`, `ruff`
- `install_rust()` unconditionally adds `~/.cargo/bin` to the process PATH, regardless of whether rust was already installed, so that subsequent installer steps can invoke `cargo` within the same run.
- Git configured via `git config --global` for `delta` (`alias.dd`,
  `alias.dl`) and `difft` (`difftool.difftastic.cmd` using
  `$HOME/.cargo/bin/difft` to avoid PATH issues, `difftool.prompt`,
  `alias.dft`, `difftastic.color`, `pager.difftool`). Aliases only; default
  git behaviour unchanged.
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
  - `parent` field alone does not create an install dependency; only `requires` does.
  - Prerequisites are resolved transitively (if C requires B and B requires A, selecting C pulls in both).
  - Deselecting an item removes its auto-selected prerequisite when no other selected item needs it.
  - A prerequisite independently selected by the user is retained when dependent items are deselected.
  - `--only` and `--skip` flag subsets are resolved correctly.
  - `InstallItem` `parent` field defaults to `None`.
- `--only`/`--skip` accept full ids only; unknown ids are rejected with an error.
- `--list` output contains id only.

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
- `unattended-upgrades` and `all-upgrades` configuration (requires apt and systemd).
