# Design: TUI Status Hints
**Status: Approved**

## Approach

Two new capabilities are added to `install.py`:

**1. Per-item install check**

`InstallItem` gains an optional `install_check: Callable[[], bool] | None = None` field. When set, it is called at TUI startup to determine whether the tool is already present. This keeps detection logic co-located with each item's definition and makes it independently testable.

**2. Container detection**

A new `in_container() -> bool` function probes the environment using `systemd-detect-virt --container --quiet` (exit code 0 = in container). Falls back to checking `/run/.containerenv` (Podman) and `/.dockerenv` (Docker) if the command is unavailable.

**3. Item state computation**

A new `compute_item_hints(items) -> dict[str, tuple[bool, str | None]]` function is called once before the TUI launches. It returns `{item_id: (default_selected, hint)}` where `hint` is a short annotation string (e.g. `"installed"`, `"already in container"`) or `None`. The computation:
- Calls each item's `install_check()` if present; if True → `(False, "installed")`
- For `incus` specifically, also checks `in_container()`; if True → `(False, "already in container")`
- Otherwise, preserves the item's existing `default_selected` with no hint

The result dict is passed into `run_selection_menu`, which uses it in `_make_selections()` to:
- Set `initial_state` from the computed bool (overriding `item.default_selected` where appropriate)
- Append `  [dim]<hint>[/dim]` to the label when a hint is present

The `InstallerApp._user_selected` initial value is likewise derived from the computed states, not raw `default_selected`.

## Tasks

1. ✓ Tests: Add unit tests for `in_container()` (mocking subprocess and env files)
2. ✓ Tests: Add unit tests for `compute_item_hints()` (installed → deselected + hint; not installed → unchanged; incus in container → deselected + hint)
3. ✓ Impl: Add `install_check: Callable[[], bool] | None` field to `InstallItem`
4. ✓ Impl: Implement `in_container()`
5. ✓ Impl: Implement `compute_item_hints()`
6. ✓ Impl: Wire `install_check` callables onto each item in `_items()`
7. ✓ Impl: Thread hint dict through `run_selection_menu` → `_make_selections()` and `InstallerApp.__init__`
8. ✓ Verify: Run `./tests/unit.py`
9. ✓ Process: Confirm ready to archive
