# Design: build-essential Unconditional Install
**Status: Ready for Review**

## Approach
Split `install_rust()` so that `build-essential` is installed in its own
`task` block before the `is_installed("rustc")` early-return guard. This
mirrors the pattern used in `install_pyright()` for `libatomic1`, and means
`build-essential` is always installed whether or not Rust is already present.

The apt invocation is idempotent, so running it on a system where
`build-essential` is already installed is harmless.

No test changes are needed — the integration test already exercises a fresh
install path. The existing `rustc` compilation smoke test (added in
2026-02-22-rust-gcc-dependency) covers the linker being present.

## Tasks
- [x] Move `build-essential` apt install into its own `task` block before the `rustc` presence check in `install_rust()` in `install.py`
- [x] Confirm implementation complete and ready to archive
