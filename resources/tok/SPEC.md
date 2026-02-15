# Specification: `tok` Script

## Overview
This command can be initialised with a secret (the *tok*en), which it encrypts against a supplied passphrase and stores on disk. When requested it prompts for the passphrase, decrypts the secret and copies it to the system clipboard (e.g. using `xclip` or `wl-copy`). After that it doesn't exit, but waits for a default of 10 seconds before overwriting the clipboard.

## Usage
- `tok --add` or `tok -a`
	- Adds a new secret, prompting for the secret to be pasted in, then the passphrase
	- The first secret is known as the 'default' secret
	- For any subsequent secrets it asks for a single word name
- `tok`
	- Requests the default secret, or if one doesn't exist, prints help
	- Prompts for the passphrase for the default secret
- 'tok <secret name>'
	- As with 'tok' but for a given secret name
- 'tok --list' or 'tok -l'
	- Lists all available secrets
- The flag `--time` or `-t` allows the user to specify the time (seconds) before the clipboard will be cleared.

## Implementation
- A minimal Python script (run via `uv`), following POS style.
- Attempts to detect if the terminal is running on X11, Wayland, or Windows and chooses the appropriate system clipboard tool.
- Uses a ubiquitous and well regarded encryption tool.
- Is written in a style so that it would be easy to see how the secret can be decrypted manually on the command line.
- Passphrases must not appear in the process argument list (i.e. avoid `-pass pass:<passphrase>`). Use `-pass stdin` to pipe the passphrase via stdin instead, keeping it out of `/proc/*/cmdline`.
- Rather than implement a method to manage the encrypted secrets within `tok`, they are stored as individual `.enc` files in `~/.local/share/tok/` and can be manually renamed, added to, or deleted. This means the encrypted files on disk need to indicate the name of the secret they relate to (e.g. `default`).
- Supports a `--stdout` flag that outputs the decrypted secret to stdout instead of the clipboard (skips the clipboard-clear timer). Enables automated testing and piping.
- If interrupted (SIGINT, SIGTERM, SIGHUP) while waiting to clear the clipboard, clears it immediately before exiting.

## Testing

- Tests run directly (no container needed — `tok` has no system-level side effects).

### Test scenarios
- Encrypt/decrypt round-trip: add a secret, retrieve it with `--stdout`, verify output matches.
- Named secrets: add multiple secrets, retrieve each by name.
- Listing: `--list` shows all stored secret names.
- Wrong passphrase: decryption fails with a clear error.
- Missing secret: requesting a non-existent name fails with a clear error.
- Signal cleanup: clipboard is cleared when tok is terminated during the wait period (tested with a fake xclip).

### Not tested
- Clipboard copy and clear behaviour (requires display server).
- Clipboard tool detection (X11/Wayland/Windows).
