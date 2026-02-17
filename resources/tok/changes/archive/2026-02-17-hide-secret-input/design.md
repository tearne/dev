# Hide Secret Input — Design

## Approach

The secret is currently read on line 84 of `tok.py` via `sys.stdin.readline()`, which echoes input to the terminal. The passphrase, by contrast, is read via the `read_passphrase()` helper (line 48), which uses `getpass.getpass()` — this reads from `/dev/tty` with echo disabled, falling back to stdin with a warning when `/dev/tty` is unavailable (e.g. in tests).

The fix is to read the secret through the same helper, giving it a prompt that reassures the user their input won't be visible. This replaces the manual `isatty()` check and `stdin.readline()` on lines 81–84.

Since the helper is now used for both secrets and passphrases, it is renamed from `read_passphrase` to `read_hidden` to reflect its general purpose.

The `--add` argparse help string is also updated to indicate the command is interactive.

The existing tests pipe input via stdin (no `/dev/tty`), so the helper takes its fallback path and reads from stdin — no test changes are needed.

## Tasks
1. Rename `read_passphrase` to `read_hidden` and update all call sites
2. Read secret via `read_hidden("Enter secret (input hidden): ")` instead of `sys.stdin.readline()`; update `--add` help text
3. Run tests to verify
