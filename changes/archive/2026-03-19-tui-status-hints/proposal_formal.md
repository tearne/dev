# Proposal: TUI Status Hints
**Status: Approved**

## Intent

The installer TUI currently presents all items with their default selection state, giving no indication of whether a tool is already present in the environment. Users must mentally track what is installed and manually deselect items they do not need re-installed. This wastes time and risks redundant installations.

Similarly, `incus` is meaningless to install when the installer itself is running inside a container, yet it appears selected by default regardless of context.

## Specification Deltas

### ADDED
- At TUI startup, each item is probed to determine whether it is already installed in the current environment.
- Items that are already installed are deselected by default.
- Each item in the TUI displays a contextual info annotation (dim, alongside the item label) explaining any pre-deselection — e.g. `installed`.
- When the installer detects it is running inside a container, `incus` is deselected by default and annotated with `already in container`.
- Clipboard tools (`wl-clipboard`, `xclip`) may be deselected for two independent reasons: session type (as before) or already installed. Either condition alone is sufficient to deselect.
- All pre-deselection defaults are overridable: the user may freely re-select any item.

### MODIFIED
- `default_selected` (previously: unconditionally `True` for most items, session-conditional for clipboard tools) is now also set to `False` automatically when an item is detected as already installed, or when environment context makes the item inappropriate (e.g. `incus` inside a container).
