# External Symlink Update
**Type**: Fix

## Intent

When upgrading an external script to a new SHA, the installer warns "already exists, not overwriting" and leaves the old symlink in place rather than updating it. The guard was intended to protect manually-placed binaries; a symlink should always be replaced.

## Approach

In `install_external_script`, if `~/.local/bin/<name>` already exists:

- **Symlink resolving into `~/.local/share/dev-installer/external/`** — replace it; it was placed by this installer and points to an older SHA's cache directory. Updating it to point at the new SHA is safe and expected.
- **Symlink pointing elsewhere** — warn and leave it; it belongs to something else.
- **Regular file** — warn and leave it; it is a user-placed binary that the installer should not clobber.

The dangling-symlink branch (lines 582–584) becomes redundant once any symlink is replaced unconditionally.

## Plan

- [x] FIX: Update the destination-exists guard in `install_external_script` to replace any existing symlink unconditionally, warning only for non-symlink files
- [x] TEST: Run `./tests/unit.py` and `./tests/integration.py`

## Conclusion

Updated `install_external_script` to replace a symlink at the destination if it resolves into the installer's own cache directory (`~/.local/share/dev-installer/external/`). Dangling symlinks are also replaced. A symlink pointing elsewhere, or a regular file, triggers a warning and is left untouched. Two new unit tests cover the added cases. 77/77 unit tests and 23/23 integration checks pass.
