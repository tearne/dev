# devenv

Dev environment setup for Ubuntu/Debian. Installs tools, configs, and helper scripts in one command.

## What it installs

- **Tools**: uv, Rust (via rustup), Helix editor, Zellij, htop, btop, incus
- **Language servers**: harper-ls, pyright, ruff
- **Configs**: Helix (config + languages), `.local/bin` on PATH
- **Scripts**: `tok` — encrypted secret manager (clipboard with auto-clear), fetched from its own repository at a pinned version

## Usage

```sh
./bootstrap_inst.sh
```

This bootstraps `uv` and `curl` if missing, then runs `install.py`. Idempotent — safe to re-run.

If `uv` is already installed:

```sh
./install.py
```

## Adding external scripts

Scripts from other repositories can be added to the installer via `external_scripts.toml`:

```toml
[[script]]
url        = "https://github.com/example/tool.git"
sha        = "<full commit SHA>"
entrypoint = "tool.py"
rename     = "tool"   # optional; defaults to entrypoint stem
```

Each entry is pinned to a specific commit SHA — only that version will ever be installed.
Updating a pin is a deliberate, reviewable change to this repository. The fetched source is
cached under `~/.local/share/dev-installer/external/` and symlinked into `~/.local/bin/`.