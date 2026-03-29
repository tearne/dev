#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# ///
"""Host-based integration test for install.py. No container required."""

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
INSTALL_PY  = SCRIPT_DIR / "install.py"
RESOURCES   = SCRIPT_DIR / "resources"
EXTERNAL_TOML = SCRIPT_DIR / "external_scripts.toml"

ALWAYS_SKIP = {
    "htop", "btop", "wl-clipboard", "xclip",
    "incus", "unattended-upgrades", "all-upgrades", "helix",
}
SKIP_WITHOUT_GCC = {
    "build-essential", "rust", "rust-analyzer", "cargo-binstall",
    "zellij", "delta", "difft", "harper-ls", "markdown-oxide",
}
SKIP_WITHOUT_LIBATOMIC = {"pyright"}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_failures = 0
_total    = 0


def passed(label: str) -> None:
    global _total
    _total += 1
    print(f"  PASS: {label}")


def failed(label: str, detail: str = "") -> None:
    global _failures, _total
    _failures += 1
    _total    += 1
    suffix = f" — {detail}" if detail else ""
    print(f"  FAIL: {label}{suffix}")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

def build_env(tmp: Path) -> dict:
    cargo_home    = tmp / ".cargo"
    uv_tools      = tmp / ".uv" / "tools"
    uv_bin        = tmp / ".uv" / "bin"
    local_bin     = tmp / ".local" / "bin"
    original_path = os.environ.get("PATH", "")
    env = os.environ.copy()
    real_rustup_home = os.environ.get("RUSTUP_HOME") or str(Path.home() / ".rustup")
    env.update({
        "HOME":           str(tmp),
        "CARGO_HOME":     str(cargo_home),
        "RUSTUP_HOME":    real_rustup_home,
        "UV_TOOL_DIR":    str(uv_tools),
        "UV_TOOL_BIN_DIR": str(uv_bin),
        "PATH":           f"{cargo_home}/bin:{uv_bin}:{local_bin}:{original_path}",
        "VIRTUAL_ENV":    "1",
    })
    return env


def selected_items(env: dict) -> list[str]:
    skip = set(ALWAYS_SKIP)
    if not shutil.which("gcc"):
        skip |= SKIP_WITHOUT_GCC
    if not shutil.which("libatomic1") and not Path("/usr/lib/x86_64-linux-gnu/libatomic.so.1").exists():
        skip |= SKIP_WITHOUT_LIBATOMIC
    result = subprocess.run(
        ["uv", "run", str(INSTALL_PY), "--list"],
        capture_output=True, text=True, env=env,
    )
    all_items = []
    for line in result.stdout.splitlines():
        # --list prints a Rich table; data rows look like: │ <id>                │
        if line.startswith("│"):
            cell = line.strip("│").strip()
            if cell and cell != "ID":
                all_items.append(cell)
    return [item for item in all_items if item not in skip]


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def run_installer(items: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", str(INSTALL_PY), "--only"] + items,
        capture_output=True, text=True, env=env,
    )


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_tool_callability(items: list[str], env: dict) -> None:
    section("Tool callability")
    tool_map = {
        "rust":            "rustc",
        "cargo-binstall":  "cargo-binstall",
        "rust-analyzer":   "rust-analyzer",
        "tok":             "tok",
        "build-essential": "gcc",  # meta-package; check its primary deliverable
    }
    for item in items:
        tool = tool_map.get(item, item)
        result = subprocess.run(
            f"command -v {tool}", shell=True, capture_output=True, env=env,
        )
        if result.returncode == 0:
            passed(f"{tool} on PATH")
        else:
            failed(f"{tool} on PATH")

    if "pyright" in items:
        result = subprocess.run(
            "pyright --version", shell=True, capture_output=True, text=True, env=env,
        )
        if result.returncode == 0:
            passed("pyright --version succeeds")
        else:
            failed("pyright --version succeeds", result.stderr.strip())

    if "rust" in items:
        result = subprocess.run(
            "echo 'fn main(){}' | rustc - -o /tmp/rust-smoke && /tmp/rust-smoke",
            shell=True, capture_output=True, text=True, env=env,
        )
        if result.returncode == 0:
            passed("rustc compiles and links successfully")
        else:
            failed("rustc compiles and links successfully", result.stderr.strip())


def verify_symlinks(items: list[str], tmp: Path) -> None:
    section("Symlinks")

    with EXTERNAL_TOML.open("rb") as f:
        data = tomllib.load(f)
    tok_sha = next(e["sha"] for e in data["script"] if e.get("rename") == "tok" or Path(e["entrypoint"]).stem == "tok")

    checks = [
        (tmp / ".local/bin/tok", f"../share/dev-installer/external/tok/{tok_sha}/tok.py", "tok symlink"),
    ]
    if "helix" in items:
        checks += [
            (tmp / ".config/helix/config.toml",   "../../setup/resources/helix/config.toml",    "config.toml symlink"),
            (tmp / ".config/helix/languages.toml", "../../setup/resources/helix/languages.toml", "languages.toml symlink"),
        ]
    for path, expected, label in checks:
        if not path.is_symlink():
            failed(label, f"{path} is not a symlink")
            continue
        actual = os.readlink(path)
        if actual == expected:
            passed(label)
        else:
            failed(label, f"expected {expected!r}, got {actual!r}")


def verify_shell_config(tmp: Path) -> None:
    section("Shell config")

    for name in (".profile", ".bashrc"):
        f = tmp / name
        text = f.read_text() if f.exists() else ""
        if 'PATH="$HOME/.local/bin:$PATH"' in text or ".local/bin" in text:
            passed(f".local/bin on PATH in {name}")
        else:
            failed(f".local/bin on PATH in {name}")

    # EDITOR conflict guard: pre-seeded EDITOR=vim should not be overwritten
    for name in (".profile", ".bashrc"):
        f = tmp / name
        text = f.read_text() if f.exists() else ""
        if "EDITOR=hx" in text:
            failed(f"EDITOR conflict guard in {name} — EDITOR=hx was written despite EDITOR=vim being present")
        else:
            passed(f"EDITOR conflict guard in {name}")


def verify_config_content() -> None:
    section("Config content")

    config = RESOURCES / "helix" / "config.toml"
    if 'theme = "autumn"' in config.read_text():
        passed('config.toml contains theme = "autumn"')
    else:
        failed('config.toml contains theme = "autumn"')

    languages = RESOURCES / "helix" / "languages.toml"
    if 'dialect = "British"' in languages.read_text():
        passed('languages.toml contains dialect = "British"')
    else:
        failed('languages.toml contains dialect = "British"')


def verify_config_not_overwritten(items: list[str], env: dict, tmp: Path) -> None:
    section("Config-not-overwritten")

    if "helix" not in items:
        return

    config_dst = tmp / ".config" / "helix" / "config.toml"
    if not config_dst.exists():
        failed("config-not-overwritten (config.toml not present, skipping)")
        return

    config_dst.unlink()
    config_dst.write_text('theme = "catppuccin"\n')

    result = run_installer(items, env)

    if 'theme = "catppuccin"' in config_dst.read_text():
        passed("existing config not overwritten")
    else:
        failed("existing config not overwritten")

    if "WARNING" in result.stdout and "not overwriting" in result.stdout:
        passed("warning emitted for existing config")
    else:
        failed("warning emitted for existing config")


def verify_install_log() -> None:
    section("Install log")

    log = SCRIPT_DIR / "install.log"
    if log.exists():
        passed("install.log exists")
    else:
        failed("install.log exists")
        return

    text = log.read_text()
    if "\033[" in text:
        failed("install.log contains no ANSI escapes")
    else:
        passed("install.log contains no ANSI escapes")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    with tempfile.TemporaryDirectory(prefix="install-test-") as tmp_str:
        tmp = Path(tmp_str)
        env = build_env(tmp)

        # Pre-seed EDITOR in shell configs to test the conflict guard
        for name in (".profile", ".bashrc"):
            f = tmp / name
            f.write_text("export EDITOR=vim\n")

        items = selected_items(env)
        print(f"Selected items: {', '.join(items)}")

        print("\n=== Running installer ===")
        result = run_installer(items, env)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            print("Installer exited with non-zero status — some checks may fail.")

        verify_tool_callability(items, env)
        verify_symlinks(items, tmp)
        verify_shell_config(tmp)
        verify_config_content()
        verify_config_not_overwritten(items, env, tmp)
        verify_install_log()

    print(f"\n{'All' if _failures == 0 else _failures} of {_total} checks {'passed' if _failures == 0 else 'failed'}.")
    sys.exit(0 if _failures == 0 else 1)


if __name__ == "__main__":
    main()
