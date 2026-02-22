#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# ///

import subprocess
import sys
import os
import re
import shutil
import getpass
import difflib
from pathlib import Path
from contextlib import contextmanager

if not (os.environ.get("VIRTUAL_ENV") or os.environ.get("UV_INTERNAL__PARENT_INTERPRETER")):
    print("Error: run this script via './install.py' or bootstrap_inst.sh, not directly.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Comment out any tool you don't want installed
# ---------------------------------------------------------------------------

def install():
    install_htop()
    install_btop()
    install_unattended_upgrades()
    install_incus()
    init_incus()
    install_rust()
    install_zellij()
    install_helix()
    install_harper_ls()
    install_pyright()
    install_ruff()
    install_tok()
    setup_local_bin_path()


# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

def install_htop():
    with task("htop"):
        if is_installed("htop"):
            log("already installed, skipping")
            return
        sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq htop")
        log("done")


def install_btop():
    with task("btop"):
        if is_installed("btop"):
            log("already installed, skipping")
            return
        sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq btop")
        log("done")


def install_unattended_upgrades():
    with task("unattended-upgrades"):
        if not is_installed("unattended-upgrades"):
            sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq unattended-upgrades")
            log("installed")
        else:
            log("already installed, skipping")

        override = Path("/etc/apt/apt.conf.d/99unattended-upgrades-override")
        if override.exists():
            log("origins already configured, skipping")
            return

        # Override file extending automatic updates to all pre-existing repositories,
        # not just security (the default in 50unattended-upgrades). The 99 prefix
        # gives it priority; 50unattended-upgrades is left untouched by this install.
        # To restore the default security-only behaviour, delete this file.
        tmp = Path("/tmp/99unattended-upgrades-override")
        tmp.write_text('Unattended-Upgrade::Allowed-Origins {\n\t"*:*";\n};\n')
        sudo(f"mv {tmp} {override}")
        log("origins configured")


def install_incus():
    with task("incus"):
        if is_installed("incus"):
            log("already installed, skipping")
            return
        sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq incus")
        log("done")


def init_incus():
    has_zfs = subprocess.run("command -v zfs", shell=True, capture_output=True).returncode == 0
    backend = "zfs" if has_zfs else "dir"

    with task(f"incus init ({backend})"):
        sudo("systemctl start incus.service")
        if subprocess.run("incus storage show default", shell=True, capture_output=True).returncode == 0:
            log("already initialized, skipping")
            return
        sudo(f"incus admin init --auto --storage-backend={backend}")
        log("done")


def install_rust():
    with task("build-essential"):
        # Required by rustup (C linker + headers); install unconditionally
        sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq build-essential")
        log("done")

    with task("Rust + Cargo + rust-analyzer"):
        if is_installed("rustc"):
            log("already installed, skipping")
            return
        run("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y")
        cargo_bin = Path.home() / ".cargo" / "bin"
        os.environ["PATH"] = str(cargo_bin) + ":" + os.environ["PATH"]
        run("rustup component add rust-analyzer")
        log("done")


def ensure_cargo_binstall():
    if is_installed("cargo-binstall"):
        return
    with task("cargo-binstall"):
        run("curl -L --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash")


def install_zellij():
    with task("Zellij"):
        if is_installed("zellij"):
            log("already installed, skipping")
            return
        ensure_cargo_binstall()
        run("cargo binstall --no-confirm zellij")
        log("done")


def install_helix():
    with task("Helix editor"):
        if is_installed("hx"):
            log("already installed, skipping")
            _link_helix_config()
            return

        with task("downloading latest .deb"):
            run(r"""curl -s https://api.github.com/repos/helix-editor/helix/releases/latest | grep -oP '"browser_download_url": "\K[^"]*amd64\.deb' | xargs curl -Lo /tmp/helix.deb""")

        with task("installing"):
            sudo("dpkg -i /tmp/helix.deb")
            run("rm /tmp/helix.deb")
            log("done")

        _link_helix_config()


def _link_helix_config():
    configs = [
        ("config.toml", "helix config"),
        ("languages.toml", "helix languages"),
    ]
    for filename, label in configs:
        with task(label):
            src = SCRIPT_DIR / "resources" / "helix" / filename
            dst = Path.home() / ".config" / "helix" / filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                if dst.is_symlink() and dst.resolve() == src.resolve():
                    log("symlink already correct")
                    continue
                if dst.is_symlink() and not dst.exists():
                    log(f"replacing dangling symlink {dst}")
                    dst.unlink()
                else:
                    diff = _config_diff(src, dst)
                    if diff is None:
                        log(f"{dst} exists with equivalent content, skipping")
                        continue
                    warn(f"{dst} differs from installable config, not overwriting (delete and rerun to update)", diff=diff)
                    continue
            rel = os.path.relpath(src, dst.parent)
            os.symlink(rel, dst)
            log(f"symlinked {dst} -> {rel}")


def install_harper_ls():
    with task("harper-ls"):
        if is_installed("harper-ls"):
            log("already installed, skipping")
            return
        ensure_cargo_binstall()
        run("cargo binstall --no-confirm harper-ls")
        log("done")


def install_pyright():
    with task("pyright"):
        if is_installed("pyright"):
            log("already installed, skipping")
            return
        # pyright-python downloads a prebuilt Node.js binary (via nodeenv). Node 25+
        # requires libatomic1, which is absent from minimal Debian/Ubuntu images.
        # https://github.com/nodejs/node/issues/60790
        sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libatomic1")
        run("uv tool install pyright")
        log("done")


def install_ruff():
    with task("ruff"):
        if is_installed("ruff"):
            log("already installed, skipping")
            return
        run("uv tool install ruff")
        log("done")


def setup_local_bin_path():
    with task("~/.local/bin on PATH"):
        profile = Path.home() / ".profile"
        marker = 'PATH="$HOME/.local/bin:$PATH"'
        if profile.exists() and marker in profile.read_text():
            log("already configured")
            return
        with open(profile, "a") as f:
            f.write(f'\n# Added by install.py\nexport {marker}\n')
        log(f"appended to {profile}")


def install_tok():
    with task("tok"):
        src = SCRIPT_DIR / "resources" / "tok" / "tok.py"
        dst = Path.home() / ".local" / "bin" / "tok"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            if dst.is_symlink() and dst.resolve() == src.resolve():
                log("symlink already correct")
                return
            if dst.is_symlink() and not dst.exists():
                log(f"replacing dangling symlink {dst}")
                dst.unlink()
            else:
                warn(f"{dst} already exists, not overwriting")
                return
        rel = os.path.relpath(src, dst.parent)
        os.symlink(rel, dst)
        log(f"symlinked {dst} -> {rel}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

_indent = 0
_password = None
_warnings = []
_logfile = None
_ansi_re = re.compile(r"\033\[[0-9;]*m")  # strip ANSI escapes for log file
SCRIPT_DIR = Path(__file__).resolve().parent


def log(msg):
    prefix = "  " * _indent
    for line in msg.splitlines():
        print(f"{prefix}{line}", flush=True)
        if _logfile:
            _logfile.write(_ansi_re.sub("", f"{prefix}{line}") + "\n")


def warn(msg, diff=None):
    log(f"WARNING: {msg}")
    _warnings.append((msg, diff))


def _config_diff(src, dst):
    """Compare two config files ignoring whitespace.
    Returns unified diff string if they differ, None if equivalent."""
    src_lines = src.read_text().splitlines()
    dst_lines = dst.read_text().splitlines()
    if [l.strip() for l in src_lines] == [l.strip() for l in dst_lines]:
        return None
    return "\n".join(difflib.unified_diff(
        dst_lines, src_lines,
        fromfile=str(dst), tofile=str(src),
        lineterm="",
    ))


@contextmanager
def task(name):
    global _indent
    log(f"▶ {name}")
    _indent += 1
    try:
        yield
    finally:
        _indent -= 1


def _stream_output(proc):
    prefix = "  " * _indent
    had_output = False
    for line in proc.stdout:
        line = line.rstrip("\n")
        sys.stdout.write(f"\033[2K\r{prefix}{line}")
        sys.stdout.flush()
        if _logfile:
            _logfile.write(f"{prefix}{line}\n")
        had_output = True
    if had_output:
        sys.stdout.write("\n")
    proc.wait()


def run(cmd):
    log(f"\033[2m$ {cmd}\033[0m")
    proc = subprocess.Popen(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    _stream_output(proc)
    if proc.returncode != 0:
        log(f"FAILED (exit {proc.returncode}): {cmd}")
        sys.exit(1)


def sudo(cmd):
    if os.geteuid() == 0:
        run(cmd)
    elif _password is None:
        run(f"sudo {cmd}")
    else:
        log(f"\033[2m$ {cmd}\033[0m")
        full = f"sudo -S {cmd}"
        proc = subprocess.Popen(
            full, shell=True, text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        proc.stdin.write(_password + "\n")
        proc.stdin.close()
        _stream_output(proc)
        if proc.returncode != 0:
            log(f"FAILED (exit {proc.returncode}): {cmd}")
            sys.exit(1)


def init_password():
    global _password
    if os.geteuid() == 0:
        return
    if subprocess.run("sudo -n true", shell=True, capture_output=True).returncode == 0:
        return
    _password = getpass.getpass("Enter sudo password: ")
    result = subprocess.run(
        "sudo -S true", shell=True, text=True,
        input=_password + "\n",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        print("Error: incorrect password.")
        sys.exit(1)


def is_installed(cmd):
    return shutil.which(cmd) is not None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _logfile
    _logfile = open(SCRIPT_DIR / "install.log", "w")

    with task("Dev environment setup"):
        init_password()

        with task("apt update"):
            sudo("DEBIAN_FRONTEND=noninteractive apt-get update -qq")

        install()

    if _warnings:
        log("")
        log("Warnings:")
        for msg, diff in _warnings:
            log(f"  - {msg}")
            if diff:
                for line in diff.splitlines():
                    log(f"    {line}")

    log("Setup complete.")
    _logfile.close()


if __name__ == "__main__":
    main()
