# Design: Fix Cargo PATH for Pre-installed Rust
**Status: Approved**

## Approach

Three small, independent changes:

**1. Unit test** (TDD — written first)
Add a test to `tests/unit.py` that calls `install_rust()` with `is_installed` monkeypatched to return `True` (simulating pre-installed rust) and `sudo`/`run` monkeypatched to no-ops. After the call, assert that `~/.cargo/bin` appears in `os.environ["PATH"]`. The existing `reset_install_state` fixture already redirects HOME to `tmp_path`, so `Path.home() / ".cargo" / "bin"` resolves correctly.

**2. Fix `install_rust()`**
Move the two PATH-update lines out of the "already installed" branch, placing them unconditionally just before the `with task("Rust"):` block. Guard with a membership check to avoid duplicating the entry on re-runs:
```python
cargo_bin = Path.home() / ".cargo" / "bin"
if str(cargo_bin) not in os.environ["PATH"]:
    os.environ["PATH"] = str(cargo_bin) + ":" + os.environ["PATH"]
```

**3. SPEC constraint**
Add one bullet to the Constraints section of `SPEC.md`:
> `install_rust()` unconditionally adds `~/.cargo/bin` to the process PATH, regardless of whether rust was already installed.

## Tasks
1. Write failing unit test for `install_rust()` PATH update when rust is pre-installed
2. Fix `install_rust()` to unconditionally update PATH (test should now pass)
3. Add constraint bullet to `SPEC.md`
4. Run unit tests to verify
5. Confirm implementation complete and ready to archive
