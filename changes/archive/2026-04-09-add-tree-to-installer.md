# Add Tree to Installer

## Intent
`tree` is missing from the installer. Users setting up a new environment have to install it manually after the fact.

## Approach
`tree` follows the same pattern as `htop` and `btop`: installed via apt, placed under the `Resource` group, with `install_check="tree"` and `uses_sudo=True`.

Changes required:
- `install.py`: add `install_tree()` function; add `InstallItem` entry in `_items()` under `parent="Resource"`
- `SPEC.md`: add `tree` to the tools list under `[Resource]` and to the apt constraints list

No new dependencies or ordering requirements. No versioning applies.

Both files were edited ahead of this process — the Plan includes a review task to verify those edits are correct. Review cadence: at the end.

## Plan
- [x] REVIEW `install.py`: verify `install_tree()` function is correct and consistent with `install_htop()`/`install_btop()`
- [x] REVIEW `install.py`: verify `InstallItem` for `tree` is correctly placed under `parent="Resource"` with `install_check="tree"` and `uses_sudo=True`
- [x] UPDATE `SPEC.md`: add `tree` to the apt constraints list

## Conclusion
Both `install.py` edits were already in place and correct. Added `tree` to the apt constraints list in `SPEC.md`.
