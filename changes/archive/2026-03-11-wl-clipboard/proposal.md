# Proposal: Clipboard Tools
**Status: Approved**

## Intent
Clipboard integration for tools such as Helix and zellij requires session-appropriate clipboard utilities. Without them, copy/paste between the terminal and the system clipboard does not work. The installer should include the correct clipboard package based on the detected session type.

## Specification Deltas

### ADDED
- A `[Clipboard]` group (under `[System]`) contains two selectable items: `wl-clipboard` (for Wayland) and `xclip` (for X11), both installed via apt.
- At install time, the session type is detected (via `WAYLAND_DISPLAY` or `XDG_SESSION_TYPE`). The appropriate item is pre-selected; the other is deselected by default. When no session type is detected (e.g. headless), both are deselected by default.
- Both items remain individually selectable/deselectable in the TUI regardless of the default.

## Scope
- **In scope**: Wayland and X11 session detection; conditional pre-selection of `wl-clipboard` or `xclip`.
- **Out of scope**: clipboard configuration for specific tools; other X11 clipboard tools (`xsel`).
