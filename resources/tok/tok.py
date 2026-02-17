#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# ///

import argparse
import base64
import getpass
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

if not (os.environ.get("VIRTUAL_ENV") or os.environ.get("UV_INTERNAL__PARENT_INTERPRETER")):
    print("Error: run this script via './tok.py' or bootstrap_inst.sh, not directly.")
    sys.exit(1)

TOK_DIR = Path(os.environ.get("TOK_DIR", Path.home() / ".local/share/tok"))
TIMEOUT = 10


def _open_tty():
    """Open /dev/tty for writing so OSC 52 reaches the terminal even when stdout is redirected."""
    try:
        return open("/dev/tty", "w")
    except OSError:
        return None


def _osc52_write(payload, tty):
    """Write an OSC 52 sequence. payload is the base64-encoded data (or empty to clear)."""
    tty.write(f"\033]52;c;{payload}\a")
    tty.flush()


def clipboard_copy(data, tty):
    # printf '\033]52;c;<base64>\a' > /dev/tty
    _osc52_write(base64.b64encode(data).decode(), tty)


def clipboard_clear(tty):
    # printf '\033]52;c;\a' > /dev/tty  (empty payload clears clipboard)
    _osc52_write("", tty)


def read_hidden(prompt):
    """getpass from /dev/tty (works even when stdin is piped); falls back to stdin."""
    try:
        return getpass.getpass(prompt, stream=sys.stderr)
    except (OSError, EOFError):
        # No /dev/tty (e.g. in CI/testing) — fall back to stdin
        sys.stderr.write("Warning: password input may be echoed.\n")
        sys.stderr.write(prompt)
        sys.stderr.flush()
        line = sys.stdin.readline().rstrip("\n")
        sys.stderr.write("\n")
        return line


def main():
    parser = argparse.ArgumentParser(
        prog="tok",
        description="Encrypt and retrieve secrets via the clipboard.",
        epilog="Secrets are stored in ~/.local/share/tok/",
    )
    parser.add_argument("--add", "-a", action="store_true", help="interactively add a new secret and passphrase")
    parser.add_argument("--list", "-l", action="store_true", help="list stored secrets")
    parser.add_argument("--stdout", action="store_true",
                        help="output secret to stdout instead of clipboard")
    parser.add_argument("--time", "-t", type=int, default=TIMEOUT, metavar="N",
                        help="clipboard clear timeout in seconds (default: %(default)s)")
    parser.add_argument("name", nargs="?", default="", help="secret name (default: 'default')")
    args = parser.parse_args()

    TOK_DIR.mkdir(parents=True, exist_ok=True)

    # --- Add ---
    if args.add:
        secret = read_hidden("Enter secret (input hidden): ")

        passphrase = read_hidden("Enter passphrase: ")
        confirm = read_hidden("Confirm passphrase: ")

        if passphrase != confirm:
            sys.stderr.write("Error: passphrases do not match.\n")
            sys.exit(1)

        if not (TOK_DIR / "default.enc").is_file():
            name = "default"
        else:
            sys.stderr.write("Secret name: ")
            sys.stderr.flush()
            name = sys.stdin.readline().rstrip("\n")

        # openssl enc -aes-256-cbc -pbkdf2 -salt -pass stdin -out <file>
        subprocess.run(
            ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
             "-pass", "stdin", "-out", str(TOK_DIR / f"{name}.enc")],
            input=(passphrase + "\n" + secret).encode(),
            check=True,
        )
        sys.stderr.write(f"Secret '{name}' stored.\n")
        sys.exit(0)

    # --- List ---
    if args.list:
        for f in sorted(TOK_DIR.glob("*.enc")):
            print(f.stem)
        sys.exit(0)

    # --- Retrieve ---
    name = args.name or "default"
    enc_file = TOK_DIR / f"{name}.enc"

    if not enc_file.is_file():
        if name == "default":
            parser.print_help(sys.stderr)
        else:
            sys.stderr.write(f"Error: secret '{name}' not found.\n")
        sys.exit(1)

    passphrase = read_hidden("Passphrase: ")

    # openssl enc -aes-256-cbc -pbkdf2 -d -pass stdin -in <file>
    result = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-d",
         "-pass", "stdin", "-in", str(enc_file)],
        input=(passphrase + "\n").encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write("Error: decryption failed (wrong passphrase?).\n")
        sys.exit(1)

    secret = result.stdout.decode()

    if args.stdout:
        print(secret)
        sys.exit(0)

    tty = _open_tty()
    if not tty:
        sys.stderr.write("Error: cannot open /dev/tty for OSC 52 clipboard (use --stdout instead).\n")
        sys.exit(1)

    clipboard_copy(secret.encode(), tty)

    def cleanup(*_):
        clipboard_clear(tty)
        sys.stderr.write("Clipboard cleared.\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGHUP, cleanup)

    sys.stderr.write(f"Secret copied to clipboard. Clearing in {args.time}s...\n")
    time.sleep(args.time)
    clipboard_clear(tty)
    sys.stderr.write("Clipboard cleared.\n")


if __name__ == "__main__":
    main()
