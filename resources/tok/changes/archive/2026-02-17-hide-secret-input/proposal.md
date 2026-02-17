# Hide Secret Input

## Intent
When running `tok -a`, the secret is displayed in plain text as the user types or pastes it. Since the secret is sensitive data (just like the passphrase), it should be hidden during input.

## Scope
- **In scope**: suppressing echo when reading the secret interactively, help text clarity, prompt reassurance
- **Out of scope**: changes to passphrase handling, piped/non-TTY input behaviour

## Delta

### MODIFIED
- Interactive secret input during `--add` is not echoed to the terminal (same behaviour as passphrase input). Non-TTY behaviour is unchanged.
- The `--add` help text indicates it is an interactive process.
- The secret prompt reassures the user that their input will not be echoed.
