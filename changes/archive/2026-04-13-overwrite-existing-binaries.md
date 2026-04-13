# Overwrite Existing Binaries on Update

## Intent

When the installer places a binary (via `install_external_script` or `install_external_cargo`), it should replace whatever already exists at the destination rather than warning and skipping. The current behaviour is overly cautious: if the destination is a regular file or a symlink pointing outside the installer cache, the installer refuses to act, which blocks updates.

## Approach

Both `install_external_script` and `install_external_cargo` share the same destination-guard logic. In both, the final `else` branch (lines 652-654 and 704-706) currently warns and returns. Change this to log a message and remove the existing file so the symlink can be placed.

The two existing tests that assert the warning behaviour (`test_external_script_does_not_replace_unrelated_symlink` and `test_external_script_does_not_overwrite_real_file`) need updating to expect replacement instead of preservation.

No version bump — this is a behaviour fix, not a new feature.

## Plan

- [x] UPDATE `install_external_script` (line 652-654): replace the `else` branch that warns and returns with a log and `dst.unlink()` so the existing file is removed and the new symlink is placed
- [x] UPDATE `install_external_cargo` (line 704-706): same change as above
- [x] UPDATE `test_external_script_does_not_replace_unrelated_symlink`: expect the symlink to be replaced rather than preserved, and expect no warnings
- [x] UPDATE `test_external_script_does_not_overwrite_real_file`: expect the file to be replaced with a symlink rather than preserved, and expect no warnings
- [x] REVIEW: run full test suite and confirm all tests pass

## Conclusion

All tasks completed as planned — no deviations or surprises.
