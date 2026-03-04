# Design: External Script Repositories
**Status: Draft**

## Approach

### Registry: `external_scripts.toml`

A file at the root of this repository lists approved external scripts:

```toml
[[script]]
url        = "https://github.com/tearne/tok.git"
sha        = "<full 40-char commit SHA>"
entrypoint = "tok.py"
rename     = "tok"      # optional; defaults to entrypoint stem (e.g. "tok" from "tok.py")
```

The installed name (and TUI id) is `rename` if provided, otherwise the stem of `entrypoint`.
The installer determines the destination directory (`~/.local/bin/`). No metadata file is
required in the external repository. Pinned versions are full commit SHAs; updating a pin is a
deliberate, reviewable commit here.

### Fetch, verify, and install

Cache location: `~/.local/share/dev-installer/external/<id>/<sha>/`

On installation of an external item:
1. If the cache directory already exists, skip the fetch (idempotent, offline-friendly)
2. Otherwise: sparse-init a git repo in the cache dir, fetch the pinned SHA from the remote,
   checkout that SHA
3. Verify `git rev-parse HEAD` in the cache dir equals the pinned SHA before touching anything
   in `~/.local/bin/`
4. Read `install-meta.toml` from the cache dir to get `script` and `name`
5. Symlink `~/.local/bin/<name>` → `<cache_dir>/<script>` (relative path, same logic as
   existing symlink installers)

### Code changes to `install.py`

- Add `external: bool = False` field to `InstallItem` (defaults to `False`; no change to
  existing items)
- Add `_load_external_items()` — reads `external_scripts.toml` using `tomllib` (stdlib in
  3.12), returns `list[InstallItem]` with `external=True` and auto-generated installer callables
- Merge external items into the registry in `_items()` by calling `_load_external_items()`
- `install_external_script(id, url, sha)` — fetch/verify/symlink logic above
- TUI `_make_selections()`: external items rendered with a `[dim]\[ext][/dim]` suffix

### Migration of tok

All tok content (`tok.py`, `test.py`, `SPEC.md`, `changes/`) moves to `/root/tok` (the
`github.com/tearne/tok` repo). `install-meta.toml` is added there. After committing, the
resulting SHA is pinned in `external_scripts.toml` here.

## Tasks

1. **Migrate**: Copy tok files to the tok repo, add `install-meta.toml`, commit, record SHA
2. **Impl**: Add `external: bool` to `InstallItem`; add `_load_external_items()` and
   `install_external_script()`; merge into `_items()`; add `[ext]` label in TUI
3. **Tests**: Unit tests for external script logic (cache hit skips fetch, SHA mismatch aborts,
   idempotent symlink); update integration test tok symlink assertion to new cache path
4. **Remove**: Delete `resources/tok/` from this repo
5. **Verify**: Run `uv run --with pytest pytest tests/unit.py` — all tests pass
6. **Process**: Confirm ready to archive
