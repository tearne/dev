# Tarball Tool Installs (with Updates)

## Intent

The Helix install fails on aarch64: the current code expects an `arm64.deb` that doesn't exist upstream — Helix publishes only an `amd64.deb`, and other architectures are served as `tar.xz` archives. Helix needs to install correctly on aarch64.

The wider need is that tarball-shipped tools sit outside `apt`'s update path. Once installed they never update on their own, and that drift will worsen as more tools of this kind land. The installer should treat tarball-installed tools as a category: detect when an installed version has fallen behind upstream, surface that to the user during installer runs, and upgrade in place when asked. The mechanism should be reusable for future tarball tools rather than bolted onto Helix alone.

Tarball tools should also live under the user's home (`~/.local/bin` and a parallel state dir), matching the installer's existing user-local habits, rather than being placed system-wide.

## Approach

### Both architectures use the tarball path

amd64 moves off `.deb` onto the same `tar.xz` route used for aarch64. One install code path, no sudo, and the new update-detection path covers every user — not just aarch64. Per-arch differences collapse to the asset suffix (`x86_64-linux` vs `aarch64-linux`).

### Pre-existing system Helix is detected and warned, not removed

If `dpkg -l helix` shows a system install on entry, the installer prints a stdout warning that the new `~/.local/bin/hx` will shadow the system binary and recommends `sudo apt remove helix`. It does not act on the system install itself — uninstalling system packages on the user's behalf is outside the installer's remit.

### State layout: versioned dirs under `~/.local/share/dev-installer/tarball/<tool>/`

Each install extracts to `~/.local/share/dev-installer/tarball/<tool>/<version>/`, parallel to the existing `external/<name>/<sha>/` cache. The version directory's name *is* the recorded state — no separate version file. `~/.local/bin/<tool>` symlinks into the active version dir. On upgrade, the new version dir is materialised, the symlink swung, and the old version dir removed.

### Reusable helper, parameterised per tool

A single helper (working name `install_tarball_release`) takes the tool name, `owner/repo`, an asset-pattern template parameterised by arch, and the binary path inside the extracted tree. Helix is the first caller; future tarball tools call it the same way. The helper handles `tar.xz` and `tar.gz` (Python's `tarfile` covers both transparently).

### Update detection extends the existing head-check machinery

The Pending/AtHead/Behind/CheckFailed state types and their TUI rendering slot are reused as-is. A new release-version checker (querying the GitHub releases API for the latest tag) sits alongside `check_remote_head` and produces the same state types. The `AtHead`/`Behind` payload field is generalised from `short_sha` to a render-only `label` so version pairs and SHA prefixes can both occupy the same indicator slot. Wiring on `InstallItem` adds a `release_repo` field; presence of `release_repo` triggers the release-version check thread, mirroring how `external_url`+`external_sha` triggers the git head-check.

### SPEC.md catches up

The Constraints entry for Helix on `SPEC.md:145` is rewritten to describe the tarball path and `~/.local/bin` placement. The entry's mention of arch-aware `.deb` selection is removed.

### Out of scope

- Migrating biome and marksman to the tarball helper. They install single binaries with no extracted runtime — the helper's value (extraction + versioned dir + symlink dance) doesn't apply. They could gain release-tag update detection on their own track later.
- Non-interactive update surfacing. The existing head-check only fires in the TUI; this change keeps that boundary.

## Plan

- [x] GENERALISE — rename `short_sha: str` to `label: str` on `AtHead` and `Behind` dataclasses; update `head_state_label` and `check_remote_head` so the existing git-SHA flow still renders correctly.

- [x] ADD — `check_release_version(repo: str, installed_version: str | None) -> HeadCheckState`: queries the GitHub releases API for the latest release's `tag_name`; returns `AtHead(label=installed_version)`, `Behind(label=f"{installed_version} → {latest}")`, or `CheckFailed`. When `installed_version is None`, returns `CheckFailed` to avoid mis-flagging a fresh install as "behind."

- [x] EXTEND — add `release_repo: str | None = None` to `InstallItem`. In the TUI app's `on_mount`, fire a release-version check thread for items with `release_repo` set, mirroring the existing `external_url`+`external_sha` wiring. The installed version used in the comparison is read from the latest `~/.local/share/dev-installer/tarball/<name>/<version>/` directory present on disk (or `None` if absent).

- [x] ADD — `install_tarball_release(name: str, repo: str, asset_pattern: str, binary: str)`: resolves the latest release tag via the GitHub API, downloads the asset matching `asset_pattern` (with `{arch}` substituted), extracts it to `~/.local/share/dev-installer/tarball/<name>/<version>/`, points `~/.local/bin/<name>` at the binary inside, and removes prior version directories. Idempotent: no-op when the latest version's directory already exists. Handles `.tar.xz` and `.tar.gz` via `tarfile`.

- [x] REWRITE — `install_helix()` in `install.py`: drop the `.deb` path. On entry, if `dpkg -l helix` reports a system install, print a stdout warning that `~/.local/bin/hx` will shadow the system binary and recommend `sudo apt remove helix`. Then call `install_tarball_release("helix", "helix-editor/helix", "{arch}-linux.tar.xz", "hx")` with arch resolved to `aarch64` or `x86_64` from `platform.machine()`. Continue to call `_link_helix_config()` afterwards.

- [x] UPDATE — helix `InstallItem` at `install.py:137`: add `release_repo="helix-editor/helix"`, remove `uses_sudo=True`.

- [x] UPDATE SPEC — `SPEC.md:145`: rewrite the helix bullet to describe the tarball install (extracted to `~/.local/share/dev-installer/tarball/helix/<version>/`, symlinked into `~/.local/bin/hx`); remove the `.deb` and arch-aware-`.deb` wording.

- [x] BUMP VERSION — minor: `1.0.4` → `1.1.0` (`VERSION` constant in `install.py`).

- [x] TEST — extend `tests/unit.py` to cover the new helpers (`_tarball_state_dir`, `installed_tarball_version`, `check_release_version`, `_link_tarball_binary`, `_warn_if_dpkg_helix_present`, and `install_tarball_release` end-to-end) under the existing mocked-HOME pattern. Refactor `install_tarball_release` to use `tempfile.NamedTemporaryFile` instead of hardcoded `/tmp` so the download path can be redirected under test.

## Log

- First end-to-end install on aarch64 placed the symlink as `~/.local/bin/helix` (the tool name) instead of `~/.local/bin/hx` (the binary name). The helper used `name` for the destination filename — fixed to use `Path(binary).name`. Discovered immediately on first run; idempotent re-run repaired the symlink.
- Initial verification was a live `install.install_helix()` call against the real machine, which mutated the user's `~/.local/bin/`, state dir, and config symlinks — that wasn't the right approach for this codebase. User flagged it; reverted to the existing mocked-HOME pattern (autouse fixture in `tests/unit.py`).
- Added 19 new unit tests covering `_tarball_state_dir`, `installed_tarball_version` (empty/single/multiple), `check_release_version` (None/AtHead/Behind/two CheckFailed paths), `_link_tarball_binary` (binary-name regression + idempotent + stale replacement), `_warn_if_dpkg_helix_present` (silent vs warning), and `install_tarball_release` end-to-end (creates state, no-op when latest, replaces prior version, no real-HOME leakage).
- Refactored the helper to use `tempfile.NamedTemporaryFile` instead of hardcoded `/tmp`; fixture also sets `TMPDIR` so downloads stay under `tmp_path`.
- 96/96 unit tests pass. Integration suite skipped: helix is in its `ALWAYS_SKIP` set, so it wouldn't exercise any code touched here.

## Conclusion

Completed as planned, with two mid-build surprises both resolved in scope: the helper symlinked under the tool name instead of the binary name (fixed; regression-tested), and an initial live-install verification mutated the user's real environment (reverted to mocked-HOME tests; helper refactored to use `tempfile` so downloads can be isolated). `SPEC.md:145` updated to describe the tarball install. No `CHANGELOG` file in the project, so no changelog entry to add. Helix remains installed on the dev host from the initial verification — the user opted to keep it.

The new test section in `tests/unit.py` (`_make_test_tarball` + `_stub_release` helpers) sets a precedent for future tarball-shipped tools: stub the GitHub API and the curl download, build a real archive in-memory, exercise extraction and symlinking under `tmp_path`. Future users of `install_tarball_release` should follow that pattern.
