# Design: Fix Binstall PATH
**Status: Approved**

## Approach

Two changes:

**1. `ensure_cargo_binstall()` in `install.py`**

Add a call to `install_rust()` at the top of `ensure_cargo_binstall()`. Since
`install_rust()` is idempotent (skips rustup if `rustc` is already installed, but
always sets `PATH`), this is safe to call unconditionally. All binstall-consuming
installers already go through `ensure_cargo_binstall()`, so this single change covers
every callsite.

```python
def ensure_cargo_binstall():
    install_rust()  # ensure cargo is on PATH before any binstall operation
    if is_installed("cargo-binstall"):
        return
    install_cargo_binstall()
```

**2. `SPEC.md`**

- Add an **Installation Order** subsection to Behaviour documenting the five stages.
- Update the `install_rust()` PATH constraint sentence to reflect that
  `ensure_cargo_binstall()` is now the primary enforcement point.

## Tasks

1. ~~Add `install_rust()` call to `ensure_cargo_binstall()` in `install.py`~~
2. ~~Add Installation Order subsection to `SPEC.md` Behaviour section~~
3. ~~Update `install_rust()` PATH constraint sentence in `SPEC.md` Constraints~~
4. ~~Confirm implementation complete and ready to archive~~
