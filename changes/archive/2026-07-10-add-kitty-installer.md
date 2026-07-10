# Add Kitty Installer

**Mode:** Formal

## Intent

`kitty` (the terminal emulator) is missing from the installer. Users who want it have to install it manually, outside this project's tracked tool set.

## Approach

### Installed via the GitHub-release tarball route

Mirrors Helix's tarball route, including a warn-but-don't-act check for a pre-existing apt install.

### `install_tarball_release` gains `{version}` substitution

Kitty's asset filenames embed the version (`kitty-0.47.4-x86_64.txz`), unlike Helix's. `asset_pattern` needs a `{version}` placeholder, filled from `tag_name` with the leading `v` stripped.

### `install_tarball_release` gains support for archives with no wrapping directory

Kitty's tarball has no top-level wrapper (`bin/`, `lib/`, `share/` sit at archive root), unlike Helix's. The current strip-first-component logic would drop everything outside the misidentified "top" dir — and `bin/kitty`'s RPATH (`$ORIGIN/../lib`) means losing `lib/` breaks it. The helper needs to detect the no-wrapper case and extract as-is.

### `InstallItem` wiring

`kitty` sits under `parent="System"` (standalone, no children — like `zellij`/`incus`), with `release_repo="kovidgoyal/kitty"` and `install_tarball_release(name="kitty", repo="kovidgoyal/kitty", asset_pattern="kitty-{version}-{arch}.txz", binary="bin/kitty")`.

### `kitten` is symlinked alongside `kitty`, not a separate `InstallItem`

Same extracted tree, same `lib/` dependency — `install_tarball_release` is called again with `binary="bin/kitten"`, so the download/extract step no-ops. Bundled automatically since it's not useful without `kitty`.

### Desktop icon installed only in a graphical session

Reuses `detect_session_type()` (already backing the `wl-clipboard`/`xclip` defaults); `None` means headless/SSH. When a session is detected, `install_kitty()` symlinks kitty's shipped `.desktop` file and hicolor icons from the state dir into `~/.local/share/applications/` and `~/.local/share/icons/hicolor/...`.

## Plan

- [x] EXTEND `install_tarball_release`: support a `{version}` placeholder in `asset_pattern`, substituted from the release `tag_name` with any leading `v` stripped.
- [x] EXTEND `install_tarball_release` extraction: detect archives with no single common top-level directory and extract them as-is instead of stripping a wrapper.
- [x] ADD `_warn_if_dpkg_kitty_present()`, mirroring `_warn_if_dpkg_helix_present()`.
- [x] ADD a helper that symlinks kitty's shipped `.desktop` file and hicolor icons from the tarball state dir into `~/.local/share/applications/` and `~/.local/share/icons/hicolor/{256x256,scalable}/apps/`, called only when `detect_session_type()` is not `None`.
- [x] ADD `install_kitty()`: warns on a pre-existing apt install, installs `bin/kitty` then `bin/kitten` via `install_tarball_release`, then links the desktop icon.
- [x] ADD `InstallItem` for `kitty` in `_items()`: `parent="System"`, `install_check="kitty"`, `release_repo="kovidgoyal/kitty"`.
- [x] UPDATE SPEC.md: add `kitty (kitten)` to the `[System]` tools tree; add kitty to the GitHub-releases constraints bullet, describing the tarball route, `kitten` bundling, and conditional desktop-icon linking.
- [x] BUMP VERSION: minor `1.1.0` → `1.2.0`.
- [x] TEST: extend `tests/unit.py` to cover `{version}` substitution, no-wrapper extraction, `_warn_if_dpkg_kitty_present`, the desktop-icon helper (graphical vs headless), and `install_kitty` end-to-end under the mocked-HOME pattern.

## Log

- Kitty's ARM asset is named `arm64` (`kitty-0.47.4-arm64.txz`), not `aarch64` — unlike Helix's, whose asset naming matches `platform.machine()` directly. `install_tarball_release`'s shared `{arch}` substitution couldn't be reused as-is for kitty; `install_kitty()` resolves `arch` itself (`"arm64" if platform.machine() == "aarch64" else "x86_64"`, mirroring biome's existing local arch-translation) and bakes it into the pattern string before passing it in, leaving only `{version}` for the helper to fill.
- All 106 unit tests pass (96 pre-existing + 10 new) under the mocked-HOME pattern; no live network calls made.

## Conclusion

Completed as planned. One implementation-time deviation, already logged: kitty's ARM release asset is named `arm64` rather than `aarch64` (unlike Helix's, which matches `platform.machine()` directly), so `install_kitty()` resolves arch locally before calling the shared helper rather than relying on its `{arch}` substitution. `install_tarball_release` gained `{version}` substitution and no-wrapper-directory extraction support, both now available to future tarball-release callers beyond kitty. `SPEC.md` updated; version bumped `1.1.0` → `1.2.0`. 106/106 unit tests pass (10 new, mocked-HOME pattern, no live network calls). No `CHANGELOG` file in this project, so no changelog entry to add.
