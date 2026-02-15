#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# ///

import argparse
import getpass
import os
import shutil
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


def detect_clipboard():
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        return "wl-copy"
    if os.environ.get("DISPLAY") and shutil.which("xclip"):
        return "xclip"
    if shutil.which("clip.exe"):
        return "clip.exe"
    return None


def clipboard_copy(clip, data):
    if clip == "wl-copy":
        # echo -n <secret> | wl-copy
        subprocess.run(["wl-copy"], input=data)
    elif clip == "xclip":
        # echo -n <secret> | xclip -selection clipboard
        subprocess.run(["xclip", "-selection", "clipboard"], input=data)
    elif clip == "clip.exe":
        # echo -n <secret> | clip.exe
        subprocess.run(["clip.exe"], input=data)


def clipboard_clear(clip):
    if clip == "wl-copy":
        # wl-copy --clear
        subprocess.run(["wl-copy", "--clear"])
    elif clip == "xclip":
        # echo -n "" | xclip -selection clipboard
        subprocess.run(["xclip", "-selection", "clipboard"], input=b"")
    elif clip == "clip.exe":
        # echo -n "" | clip.exe
        subprocess.run(["clip.exe"], input=b"")


def read_passphrase(prompt):
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
    parser.add_argument("--add", "-a", action="store_true", help="add a new secret")
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
        if sys.stdin.isatty():
            sys.stderr.write("Enter secret: ")
            sys.stderr.flush()
        secret = sys.stdin.readline().rstrip("\n")

        passphrase = read_passphrase("Enter passphrase: ")
        confirm = read_passphrase("Confirm passphrase: ")

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

    passphrase = read_passphrase("Passphrase: ")

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

    clip = detect_clipboard()
    if not clip:
        sys.stderr.write("Error: no clipboard tool found (install xclip, wl-copy, or use --stdout).\n")
        sys.exit(1)

    clipboard_copy(clip, secret.encode())

    def cleanup(*_):
        clipboard_clear(clip)
        sys.stderr.write("Clipboard cleared.\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGHUP, cleanup)

    sys.stderr.write(f"Secret copied to clipboard. Clearing in {args.time}s...\n")
    time.sleep(args.time)
    clipboard_clear(clip)
    sys.stderr.write("Clipboard cleared.\n")


if __name__ == "__main__":
    main()
