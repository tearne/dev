# Guidelines

## Tests
- `tests/unit.py` — unit tests for `install.py` file-operation logic. Run with `./tests/unit.py` or `uv run --with pytest pytest tests/unit.py`. No container required.
- `tests/integration.sh` — integration test for `bootstrap_inst.sh`/`install.py`. Launches a fresh incus container, runs setup, and verifies all tools, symlinks, and configs. Incus must be initialised on the host.

