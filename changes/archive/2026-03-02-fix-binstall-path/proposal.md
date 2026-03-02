# Proposal: Fix Binstall PATH
**Status: Ready for Review**

## Intent

`cargo binstall` fails with `cargo: not found` when installing items that depend on
`cargo-binstall` (e.g. `zellij`). The root cause is that `install()` iterates items
in list order, and `zellij` appears before `rust` in `_items()`. When `zellij` calls
`ensure_cargo_binstall()`, cargo-binstall self-installs successfully but warns that
`~/.cargo/bin` is missing from `PATH`. The subsequent `cargo binstall` call then fails
because `install_rust()` — which is responsible for adding `~/.cargo/bin` to the
process `PATH` — has not yet run.

## Scope

- **In scope**: fixing `ensure_cargo_binstall()` so that `~/.cargo/bin` is always on
  `PATH` before any `cargo binstall` invocation; updating the spec to mandate logical
  installation order
- **Out of scope**: changing item list ordering; adding new items

## Delta

### ADDED

- **Installation Order** subsection (Behaviour): documents the logical stages in which
  items are installed, with explanations for ordering constraints:

  ```
  1. apt update — always runs first so package metadata is current.
  2. build-essential — apt; installed by install_rust() as a rust build dependency;
     runs before rustup so the C linker is present when the Rust toolchain links binaries.
  3. rust (rustup/rustc/cargo) — must precede cargo-binstall and rust-analyzer,
     which depend on it. install_rust() also adds ~/.cargo/bin to the process PATH.
  4. cargo-binstall — must precede all items installed via cargo binstall
     (zellij, delta, difft, harper-ls, markdown-oxide).
  5. Remaining items — no fixed relative order required among themselves.
  ```

  This order is enforced at runtime by `ensure_cargo_binstall()`, which calls
  `install_rust()` before checking or installing `cargo-binstall`. Items that consume
  binstall always go through `ensure_cargo_binstall()`, so stages 2–4 are guaranteed
  to complete before any `cargo binstall` invocation, regardless of the order items
  appear in `_items()`.

### MODIFIED

- **`ensure_cargo_binstall()` guarantee** (Constraints): currently the spec states that
  `install_rust()` unconditionally adds `~/.cargo/bin` to the process `PATH`. This is
  true but insufficient — it depends on `install_rust()` running before any
  binstall-consuming installer, which the item list order does not guarantee.

  **New**: `ensure_cargo_binstall()` calls `install_rust()` before checking or
  installing `cargo-binstall`, guaranteeing `~/.cargo/bin` is on `PATH` and rust is
  bootstrapped before any `cargo binstall` invocation, regardless of the position of
  the calling item in the list.

  The existing `install_rust()` PATH clause remains (for the direct installation path
  via the `rust` item) but is no longer solely responsible for this guarantee.
