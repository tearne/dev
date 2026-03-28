# Design: External Dependency Update Hint
**Status: Approved**

## Approach

### Data model

`InstallItem` gains two optional fields populated by `_load_external_items()`:
- `external_url: str | None = None` — the repo URL, used to initiate the remote check
- `external_sha: str | None = None` — the pinned SHA from `external_scripts.toml`, used as the source of truth for both the remote comparison and the install check

A `HeadCheckState` dataclass hierarchy represents the lifecycle of a single check:

```python
@dataclass
class Pending:
    frame: int = 0          # spinner animation index

@dataclass
class AtHead:
    short_sha: str          # first 7 chars of pinned SHA

@dataclass
class Behind:
    short_sha: str          # first 7 chars of pinned SHA

@dataclass
class CheckFailed:
    pass

HeadCheckState = Pending | AtHead | Behind | CheckFailed
```

`InstallerApp` holds `_head_states: dict[str, HeadCheckState]`, keyed by item id, initialised to `Pending()` for each external item before `compose()` runs.

### Install check

The `install_check` for external items is a callable that verifies the symlink at `~/.local/bin/<name>` resolves into the pinned SHA's cache directory (`~/.local/share/dev-installer/external/<name>/<sha>`). This ensures a SHA change in `external_scripts.toml` causes the item to be selected for reinstall.

### Label rendering

The `[ext]` label and head state indicator are combined into a single `head_state_label(state)` expression:

- `Pending`: `[dim][ext ⠋][/dim]` (spinner frame advances)
- `AtHead`: `[dim][ext a1b2c3 HEAD [/dim][green]✓[/green][dim]][/dim]`
- `Behind`: `[dim][ext a1b2c3 update available [/dim][yellow]?[/yellow][dim]][/dim]`
- `CheckFailed`: `[dim][ext ?][/dim]`

`_make_selections()` uses `head_state_label()` directly in place of the former `[dim][ext][/dim]` label. `visual_width()` adds a fixed `_INDICATOR_WIDTH` for external items to keep deselect hint padding stable across state transitions. `Selection` objects are created with `id=node_id` so that `replace_option_prompt(node_id, ...)` can locate them by id.

### Background checks

`check_remote_head(url, pinned_sha)` runs `git ls-remote <url> HEAD` via subprocess and returns `AtHead`, `Behind`, or `CheckFailed`. On `on_mount`, a daemon thread per external item calls `check_remote_head` then posts the result back to the main thread via `call_from_thread(_on_head_check_done, ...)`. `_on_head_check_done` updates `_head_states` and calls `replace_option_prompt` to refresh the label.

### Spinner animation

`on_mount` starts a repeating timer via `set_interval(0.1, _tick_spinners)`. `_tick_spinners` advances the `frame` counter for all `Pending` states and refreshes their labels. The timer is a no-op once all states have resolved.

## Tasks

1. ✓ Impl: Add `external_url` and `external_sha` to `InstallItem`; populate in `_load_external_items()`
2. ✓ Impl: Change `install_check` for external items to verify symlink resolves into pinned SHA's cache dir
3. ✓ Impl: Add `HeadCheckState` types and `head_state_label()` function
4. ✓ Impl: Add `check_remote_head()` function
5. ✓ Impl: Initialise `_head_states` in `InstallerApp.__init__()`
6. ✓ Impl: Update `_make_selections()` and `visual_width()` to use combined head state label; add `id=node_id` to `Selection`
7. ✓ Impl: Add `_on_head_check_done()` handler and `_tick_spinners()` timer callback
8. ✓ Impl: Spawn background threads and start timer in `on_mount`
9. ✓ Tests: Unit tests for `head_state_label()` (all four states)
10. ✓ Tests: Unit tests for `check_remote_head()` (match, differ, failure, empty output)
11. ✓ Tests: Unit tests for external install_check (correct SHA, wrong SHA, not installed)
12. ✓ Verify: Run `./tests/unit.py` — 79 passed
13. Process: Confirm ready to archive
