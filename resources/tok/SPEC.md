# Specification: `tok` Script

## Overview
This command can be initialised with a secret (the *tok*en), which it encrypts against a supplied passphrase and stores on disk. When requested it prompts for the passphrase, decrypts the secret and copies it to the system clipboard via OSC 52 (a terminal escape sequence supported by most modern terminals). After that it doesn't exit, but waits for a default of 10 seconds before clearing the clipboard.

## Usage
- `tok --add` or `tok -a`
	- Interactively adds a new secret and passphrase
	- The first secret is known as the 'default' secret
	- For any subsequent secrets it asks for a single word name
- `tok`
	- Requests the default secret, or if one doesn't exist, prints help
	- Prompts for the passphrase for the default secret
- `tok <secret name>`
	- As with `tok` but for a given secret name
- `tok --list` or `tok -l`
	- Lists all available secrets
- The flag `--time` or `-t` allows the user to specify the time (seconds) before the clipboard will be cleared.

## Behaviour
- Copies to the system clipboard using OSC 52 escape sequences. Works over SSH, through terminal multiplexers (e.g. Zellij), and on any OS — no clipboard tools required on the remote host.
- Clears the clipboard after the timeout by writing an empty OSC 52 sequence.
- Secrets are stored as individual `.enc` files in `~/.local/share/tok/`. Files can be manually renamed, added to, or deleted.
- `--stdout` outputs the decrypted secret to stdout instead of the clipboard, skipping the clipboard-clear timer.
- If interrupted (SIGINT, SIGTERM, SIGHUP) while waiting to clear the clipboard, clears it immediately before exiting.
- Interactive secret and passphrase input is not echoed to the terminal. The secret prompt reassures the user that their input will not be visible.
- When stdin is not a terminal (e.g. secret piped from a file), the passphrase is still prompted interactively (via `/dev/tty`). Falls back to stdin when `/dev/tty` is unavailable (e.g. automated testing), with a warning that input may be echoed.

## Constraints
- Passphrases must not appear in the process argument list (i.e. avoid `-pass pass:<passphrase>`). Use `-pass stdin` to pipe the passphrase via stdin instead, keeping it out of `/proc/*/cmdline`.
- POS style (see `DEFINITIONS.md`).
- Uses `openssl enc` for encryption — chosen so the user can see how to decrypt manually on the command line.

## Verification

- Tests run directly (no container needed — `tok` has no system-level side effects).

### Test scenarios
- Encrypt/decrypt round-trip: add a secret, retrieve it with `--stdout`, verify output matches.
- Named secrets: add multiple secrets, retrieve each by name.
- Listing: `--list` shows all stored secret names.
- Wrong passphrase: decryption fails with a clear error.
- Missing secret: requesting a non-existent name fails with a clear error.
- Signal cleanup: SIGTERM during the wait period produces a valid OSC 52 clear sequence (`\033]52;c;\a` — empty payload).

### Not tested
- Passphrase prompt when stdin is piped (requires `/dev/tty`).
