# ARM Support (Raspberry Pi 5)

## Intent
The installer currently runs only on x86_64. It should also run correctly on ARM64 hardware (Raspberry Pi 5), installing the same set of tools without manual intervention.

## Approach
Only one function requires a code change: `install_helix()` in `install.py`. It downloads the Helix `.deb` using a hardcoded `amd64` suffix; on aarch64 the correct suffix is `arm64`. The fix mirrors the pattern already used in `install_biome()`: check `platform.machine() == "aarch64"` and select the appropriate suffix before constructing the `grep` pattern.

All other tools are already architecture-transparent:
- apt packages resolve to the correct arch automatically
- rustup detects and installs the native toolchain target
- cargo-binstall selects arch-appropriate pre-built binaries, falling back to source compilation when none are available
- biome already uses `platform.machine()` to select `arm64` vs `x64`
- grit is compiled from source via cargo — no arch special-casing needed
- tok is a Python script — no arch dependency
- pyright and ruff are installed via uv — aarch64 wheels are published

`SPEC.md` requires two updates: the Overview should mention ARM64 support, and the Constraints section's helix installation note should reflect arch-aware deb selection.

No new unit tests are required: the arch-selection expression is a one-liner of the same form as the already-untested biome equivalent, and adding a test for it alone would be disproportionate. Integration tests are unaffected — they run whatever architecture the host provides.

## Plan
- [x] UPDATE IMPL — `install_helix()` in `install.py`: replace hardcoded `amd64\.deb` grep pattern with an arch-derived variable (`arm64` when `platform.machine() == "aarch64"`, else `amd64`), matching the biome pattern
- [x] UPDATE SPEC — `SPEC.md` Overview: add a note that ARM64 (aarch64 / Raspberry Pi 5) is supported alongside x86_64
- [x] UPDATE SPEC — `SPEC.md` Constraints: update the helix installation method entry to note arch-aware `.deb` selection (`amd64` or `arm64`)

## Conclusion

Replaced the hardcoded `amd64` suffix in `install_helix()` with an arch-derived variable matching the existing pattern in `install_biome()`, and updated `SPEC.md` to reflect ARM64 support in the Overview and the helix Constraints entry.
