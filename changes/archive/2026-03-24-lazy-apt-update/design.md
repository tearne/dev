# Design: Lazy apt-get update
**Status: Approved**

## Approach

Two independent behaviours are made conditional on the selected items:

**1. Lazy `apt-get update`**

A module-level `_apt_updated: bool = False` flag and an `ensure_apt_updated()` function are added. Each apt-installing function calls `ensure_apt_updated()` immediately before its `apt-get install` call; the function runs `apt-get update` at most once. The unconditional `apt update` task in `main()` is removed.

**2. Conditional sudo prompt**

`InstallItem` gains a `uses_sudo: bool = False` field. Items that call `sudo()` directly in their installer set this to `True`. A helper `needs_sudo(items, selected) -> bool` returns `True` if any selected item has `uses_sudo=True`. In `main()`, `init_password()` is called only when `needs_sudo()` is `True`, but always before the install loop begins.

Items that directly use sudo: `htop`, `btop`, `wl-clipboard`, `xclip`, `unattended-upgrades`, `all-upgrades`, `incus`, `rust`, `helix`. (`rust` uses sudo for `build-essential`; `helix` uses `dpkg -i`.)

## Tasks

1. Tests: Add unit tests for `needs_sudo()` (selected item with `uses_sudo=True` → True; none → False; empty selection → False)
2. Impl: Add `uses_sudo: bool = False` to `InstallItem`
3. Impl: Implement `needs_sudo(items, selected) -> bool`
4. Impl: Wire `uses_sudo=True` onto relevant items in `_items()`
5. Impl: Add `_apt_updated` flag and `ensure_apt_updated()`
6. Impl: Replace `apt-get install` calls in apt installers with `ensure_apt_updated()` + install; remove unconditional `apt update` from `main()`
7. Impl: Gate `init_password()` in `main()` on `needs_sudo()`
8. Verify: Run `./tests/unit.py`
9. Process: Confirm ready to archive
