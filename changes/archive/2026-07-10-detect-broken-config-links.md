# Detect Broken Config Links

**Mode:** Formal

## Intent

The installer links certain configs (currently Helix's `config.toml` and `languages.toml`) from the repo into the user's home directory. If the repo is later relocated, those links go dangling, and the affected tool silently falls back to its own defaults rather than surfacing an error. A user who reruns the installer without happening to reselect the affected item gets no signal that anything needs attention. Give the installer a way to detect links it manages that are broken, and surface that in the selection menu so the user knows to reselect the item and repair it.

## Approach

### Detection is a per-item hook, not a Helix special case

`InstallItem` gains an optional `link_check: Callable[[], bool] | None` field, returning `False` when a link the item manages is broken. Only `helix` sets it initially, but the mechanism isn't hardcoded to Helix, so any future repo-linked item can opt in the same way.

### Surfaced through the existing hint mechanism, not a new one

`compute_item_hints` already probes `install_check` once and produces `(default_selected, hint)` per item before the TUI opens. When `install_check` reports installed but `link_check` reports broken, it overrides the hint text (e.g. "config broken — reselect to repair") while leaving `default_selected` at its computed value. This reuses the existing "installed" surfacing path rather than adding a second probing pass, and keeps the earlier decision intact: broken links are surfaced, not auto-selected — an item the user deliberately left off this run isn't forced back on.

### Helix's check reuses the existing dangling-symlink test

`link_check` for `helix` tests both `config.toml` and `languages.toml` for `is_symlink() and not exists()` — the same condition `_link_helix_config`'s self-heal branch already detects. No new breakage detection logic, just exposing the existing test as a predicate the menu can call.

### Runs synchronously, not threaded like the release-version checks

The release-version indicators (`release_repo`/`external`) run on background `threading.Thread`s with a `Pending()` spinner state because they hit the network and would otherwise block the TUI for seconds. `link_check` is a local filesystem stat, the same cost class as `install_check` itself — both run inline in `compute_item_hints`, synchronously, before the TUI is built.

## Plan

- [x] Add `link_check: Callable[[], bool] | None` field to `InstallItem`
- [x] Add `helix_config_link_check()` predicate testing `config.toml` and `languages.toml` for a dangling symlink
- [x] Set `link_check=helix_config_link_check` on the `helix` item in `_items()`
- [x] In `compute_item_hints`, override the hint to a broken-link message when `install_check` passes but `link_check` fails
- [x] Add unit tests for `helix_config_link_check`
- [x] Add unit tests for the `compute_item_hints` broken-link hint override

## Log

- User-reported symptom during review: the `helix` row showed no hint at all in the real TUI, though the underlying `compute_item_hints` data was verified correct. Root cause: `_refresh_external_label` (the callback that rewrites a row's label once its background release-version check resolves) rebuilds the label from scratch and never re-appends the hint suffix that the initial render included — so any hint on an item with `release_repo`/`external` set is wiped the moment its version check completes, which happens fast enough that the hint is barely visible. This is a pre-existing bug (it silently dropped the plain "installed" hint too, just unnoticed), not something introduced by this change, but it directly blocked the new hint from being usable, so fixed it in scope: hoisted `visual_width`/`max_width`/`ordered` out of `_make_selections` into shared scope so `_refresh_external_label` can reuse them to re-append the hint. Verified via a headless Textual pilot render forcing the resolved `AtHead` state, matching exactly what the user saw on screen.

## Conclusion

Completed. Beyond the planned tasks, fixed a pre-existing bug in `_refresh_external_label` that silently dropped a row's hint text once its background release-version check resolved — without that fix, the new broken-link hint would have been effectively invisible in normal use. See the Log for detail. No project changelog exists to add an entry to.
