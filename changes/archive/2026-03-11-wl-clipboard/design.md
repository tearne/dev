# Design: Clipboard Tools
**Status: Draft**

## Approach

### Session detection
A `detect_session_type()` helper checks environment variables in order:
1. `WAYLAND_DISPLAY` set → `"wayland"`
2. `XDG_SESSION_TYPE == "wayland"` → `"wayland"`
3. `XDG_SESSION_TYPE == "x11"` → `"x11"`
4. Otherwise → `None` (headless / unknown)

Note: when invoked via `sudo`, these variables may be stripped. Detection runs against the environment as the script sees it; the user can always override via the TUI.

### Conditional default selection
`InstallItem` gains a `default_selected: bool = True` field. The two clipboard items set this based on `detect_session_type()` at `_items()` call time:
- `wl-clipboard`: `default_selected = session == "wayland"`
- `xclip`: `default_selected = session == "x11"`

### TUI changes
- `_make_selections()` uses `item.default_selected` (rather than hardcoded `True`) for each item's `initial_state`.
- `InstallerApp.__init__` initialises `_user_selected` from items where `default_selected=True` (rather than all ids).
- Group headers retain `initial_state=True`; the Clipboard group header will be deselected by child-toggle logic if both children are off. (This is acceptable — the existing toggle propagation handles it.)

### Groups and items
- New `Group("Clipboard", parent="System")` added to `_groups()`.
- Two new items added to `_items()` under `parent="Clipboard"`:
  - `wl-clipboard` → `install_wl_clipboard()`
  - `xclip` → `install_xclip()`
- Both use `apt`; both follow the standard `is_installed` skip pattern.

## Tasks
1. ✓ Tests: Add unit tests for `detect_session_type()` (wayland, x11, headless cases)
2. ✓ Tests: Add unit test — items with `default_selected=False` are excluded from the initial TUI selection set
3. ✓ Impl: Add `default_selected: bool = True` to `InstallItem`
4. ✓ Impl: Add `detect_session_type()` function
5. ✓ Impl: Add `Clipboard` group and `wl-clipboard`/`xclip` items; add `install_wl_clipboard()` and `install_xclip()`
6. ✓ Impl: Update TUI `_make_selections()` and `InstallerApp.__init__` to use `default_selected`
7. ✓ Verify: Run unit tests (`./tests/unit.py`)
8. Process: Confirm ready to archive
