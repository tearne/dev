# Rust Analyzer Install Check
**Type**: Fix
**Status**: Approved

## Log
`is_installed("rust-analyzer")` uses `shutil.which`, which finds the rustup proxy at `~/.cargo/bin/rust-analyzer` regardless of whether the component is actually installed. This causes `install_rust_analyzer` to skip `rustup component add rust-analyzer`.

Fix: replace the `shutil.which`-based check with a `rustup component list --installed` check in both the `InstallItem.install_check` and the guard inside `install_rust_analyzer`.
