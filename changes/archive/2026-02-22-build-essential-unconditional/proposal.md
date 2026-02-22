# Proposal: build-essential Unconditional Install
**Status: Ready for Review**

## Intent
The previous fix (2026-02-22-rust-gcc-dependency) placed the `build-essential`
install inside `install_rust()` after the early-return guard. If `rustc` is
already present, the function returns immediately and `build-essential` is never
installed, leaving the system without a C linker or headers.

## Scope
- **In scope**: ensuring `build-essential` is installed regardless of whether Rust is already present
- **Out of scope**: any other dependency or installer changes

## Delta

### MODIFIED
- `install_rust()` must install `build-essential` unconditionally (before or independent of the rustc presence check)
