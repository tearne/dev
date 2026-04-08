# Fix rustup Component Check on New Machine

## Intent
`bootstrap.sh` crashes on a new machine that does not have Rust installed. The `rustup_component_installed` check calls `rustup` as a subprocess; when `rustup` is absent, Python raises `FileNotFoundError` instead of treating the component as not installed. The selection menu never opens.

## Approach
In `rustup_component_installed` (install.py ~line 1084), wrap the `subprocess.run` call in a `try/except FileNotFoundError` block that returns `False`. This mirrors the intent of the check — if `rustup` is not present, the component is not installed.

Review of all other `subprocess.run` calls in install.py confirms this is the only unsafe site — all others use `shell=True`, which delegates to the shell and never raises `FileNotFoundError`.

No other changes are needed. Patch bump.

## Plan
- [x] UPDATE IMPL: wrap `subprocess.run` in `rustup_component_installed` with `try/except FileNotFoundError` returning `False`

## Conclusion
Added `try/except FileNotFoundError` around the `rustup` subprocess call in `rustup_component_installed`. When `rustup` is absent the check now returns `False`, allowing the selection menu to open normally on a new machine.
