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




## Dependencies

- `uv` will ensure Python is used at runtime.
- Python 3.12



## Configuration

No configuration for the `bootstrap_inst.sh` installer - everything hard coded, following the POS style.


## Functional Requirements

- Installation commands should clearly display the shell command that is currently running, along with a description such as "installing <tool>".  These messages should not be pushed off top of terminal.
- Idempotency - if a tool installed, skip it, if a config exists do nothing, but warn and summarise at the end of the run.
- Minimal interaction once started - user starts it and goes to get coffee.
- Error handling - fail fast, with breadcrumbs indicating on how far it got.
- Prompts for user password once at start, if required. Skips the prompt when running as root or when sudo credentials are already cached (passwordless sudo).
- Wherever possible, the tool will install its own dependencies at runtime (e.g. `uv`, `curl`).
- When installing assets, copy from a relative rather than an absolute path.

### Third-party tools to install
All latest stable versions
- `uv` (via `curl`) - bootstrapped via outer BASH script or manually by user.
- Rust, including
  - Cargo and rust analyzer (via RustUp (via `curl`)) for Helix
- Helix editor (download latest stable deb from GitHub), including language servers:
  - `harper-ls` (via `cargo binstall`)
  - `pyright` (via `uv`)
  - `ruff` (via `uv`)
- Zellij (via `cargo binstall`)
- `htop`, `btop` and `incus` (installed non-interactively via apt repos - no PPA)
- Incus initialisation (`incus admin init`) with ZFS storage backend.  Falls back to `dir` backend when ZFS is not installed.

### Scripts / Aliases to Install
- `tok` (see `resources`) to be installed in `.local/bin`

### Configuration to Set Up

#### General
- When installing a config, soft link it from the resources folder. Perform the linking operation using a relative path so it doesn't matter where the project has been checked out.
- If a symlink is dangling (target no longer exists), replace it silently.
- If config file exists, don't overwrite it. Perform a diff to determine if there is a non-whitespace difference between the existing and installable config and then:
  - Warn the user if the installable config is different and they can delete the current config and rerun if they want to overwrite.
  - Record the warning so all warnings can be summarised at the end
  - When displaying config warnings at the end of the run, show a diff

#### Specific
- Ensure that `.local/bin/` is on the users path.
- Add Helix config (via soft link to a local resources directory if possible):
  - config
    - set `true-color`
    - set `autumn` theme
    - put a ruler at 80 chars
    - set relative line numbers
    - always show the bufferline
  - languages
    - set `soft-wrap` for markdown files
  - Configure `harper-ls` to use a British English dictionary
  - Add a language server config if required to make use of the installed lsps



## Non-Functional Requirements

- Use POS style.
- Root structure to include these key files:
```
<project root>/
├── resources/  # Config files to be soft linked during installation
├── bootstrap_inst.sh  # Bash entry point, bootstraps `uv`
├── install.py         # Python logic (uv single-file script)
├── test.sh     # Incus test harness
```



## Testing

- Testing where possible without compromising the simplicity of the code.
- Testing can be undertaken within an `incus` container where relevant.
- Use the latest LTS Ubuntu for testing.

### Test Scenarios

- Test the overall installation process completes without error
- Verify each tool is callable after setup (`htop`, `btop`, `incus`, `rustc`, `cargo`, `zellij`, `hx`, `harper-ls`, `pyright`, `ruff`)
- Verify config symlinks point to the expected relative targets
- Verify config file content (`theme = "autumn"`, `dialect = "British"`)
- Check that new terminals get `.local/bin` on their path
- Test existing configs are not overwritten. Warn that they will not be overwritten and move on.

### Logging / Output

- Use a structured/hierarchical log output format, which reveals which stage/sub-stage we're at, as well as output from any processes being run.
- Create an install log file containing the commands that were run and their full output, to compensate for the single-line console display during the run. The log is overwritten on each run.



## Non-Goals

- No flags and config - just edit install.py

