# Proposal: Fix Cargo PATH for Pre-installed Rust
**Status: Ready for Review**

## Intent
When `install_rust()` skips installation because `rustc` is already present, it also skips the `os.environ["PATH"]` update that adds `~/.cargo/bin`. Subsequent `cargo binstall` calls then fail with "cargo: not found" because the subprocess environment lacks `~/.cargo/bin` on PATH.

## Scope
- **In scope**: fixing the PATH update; adding a SPEC constraint to make the invariant explicit; adding a unit test to catch regressions
- **Out of scope**: changes to how PATH is persisted to shell profiles

## Delta

### ADDED
- **Constraint**: `install_rust()` unconditionally adds `~/.cargo/bin` to the process PATH, regardless of whether rust was already installed
- **Unit test scenario**: `install_rust()` adds `~/.cargo/bin` to `os.environ["PATH"]` even when `rustc` is already installed

### MODIFIED
- `install_rust()`: PATH update for `~/.cargo/bin` moved outside the "already installed" early-return guard so it runs unconditionally
