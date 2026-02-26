#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# dependencies = [
#   "textual",
# ]
# ///

import argparse
import subprocess
import sys
import os
import re
import shutil
import getpass
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from typing import Callable

# ---------------------------------------------------------------------------
# Item model and registry
# ---------------------------------------------------------------------------

@dataclass
class InstallItem:
    id: str
    label: str
    installer: Callable
    parent: str | None = None
    requires: list[str] = field(default_factory=list)
    short_name: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.short_name:
            self.short_name = self.id


def _items() -> list[InstallItem]:
    return [
        InstallItem("htop",                  "htop",                       install_htop),
        InstallItem("btop",                  "btop",                       install_btop),
        InstallItem("unattended-upgrades",   "unattended-upgrades",        install_unattended_upgrades, short_name="upgrades", description="updates all apt repos, not security-only"),
        InstallItem("incus",                 "incus",                      install_incus_and_init),
        InstallItem("rust",                  "Rust + Cargo + rust-analyzer", install_rust),
        InstallItem("zellij",                "Zellij",                     install_zellij,   requires=["rust"]),
        InstallItem("helix",                 "Helix editor",               install_helix),
        InstallItem("harper-ls",             "harper-ls",                  install_harper_ls, parent="helix", requires=["rust"], short_name="harper"),
        InstallItem("pyright",               "pyright",                    install_pyright,   parent="helix"),
        InstallItem("ruff",                  "ruff",                       install_ruff,      parent="helix"),
        InstallItem("tok",                   "tok",                        install_tok),
    ]


# ---------------------------------------------------------------------------
# Selection logic
# ---------------------------------------------------------------------------

def resolve_selection(items: list[InstallItem], user_selected: set[str]) -> set[str]:
    """Return the full selection set given what the user explicitly selected.

    Starts from user_selected and adds any prerequisites transitively.
    Prerequisites not required by any user-selected item are excluded, so
    deselecting an item automatically drops its auto-activated prerequisites
    (unless they were also user-selected independently).
    """
    requires_map = {item.id: item.requires for item in items}
    selected = set(user_selected)

    changed = True
    while changed:
        changed = False
        for sid in list(selected):
            for req in requires_map.get(sid, []):
                if req not in selected:
                    selected.add(req)
                    changed = True

    return selected


# ---------------------------------------------------------------------------
# Install orchestration
# ---------------------------------------------------------------------------

def install(items: list[InstallItem], selected: set[str]) -> None:
    for item in items:
        if item.id in selected:
            item.installer()
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


def install_incus_and_init():
    install_incus()
    init_incus()


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
# TUI
# ---------------------------------------------------------------------------

def run_selection_menu(items: list[InstallItem]) -> set[str] | None:
    """Display the interactive selection menu.

    Returns the user_selected set on confirmation, or None if the user aborted.
    """
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.widgets import Footer, Header, SelectionList, Static
    from textual.widgets.selection_list import Selection

    all_ids = [item.id for item in items]
    parent_ids = {item.parent for item in items if item.parent}
    child_ids = {item.id for item in items if item.parent}

    def _make_selections() -> list[Selection]:
        entries = []
        for item in items:
            indent = "  " if item.parent else ""
            desc = f"  [dim]{item.description}[/dim]" if item.description else ""
            entries.append(Selection(f"{indent}{item.label}{desc}", item.id, initial_state=True))
        return entries

    class InstallerApp(App):
        BINDINGS = [
            Binding("enter",  "confirm",      "Install",  show=True,  priority=True),
            Binding("q",      "quit_abort",   "Quit",     show=True),
            Binding("escape", "quit_abort",   "Quit",     show=False),
            Binding("j",      "cursor_down",  "Down",     show=False),
            Binding("k",      "cursor_up",    "Up",       show=False),
            Binding("h",      "cursor_up",    "Up",       show=False),
            Binding("l",      "cursor_down",  "Down",     show=False),
        ]
        CSS = """
        SelectionList { height: 1fr; border: solid $accent; }
        Header { height: 1; }
        #hints { padding: 0 1; color: $text-muted; }
        """

        def __init__(self):
            super().__init__()
            self._result: set[str] | None = None
            # Track which items the user has explicitly toggled off
            # (starts fully selected; user_selected = all)
            self._user_selected: set[str] = set(all_ids)

        def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            yield SelectionList(*_make_selections(), id="menu")
            yield Static("space/click toggle  ↑↓/jk navigate  enter install  q quit", id="hints")
            yield Footer()

        def on_mount(self) -> None:
            self.title = "Dev Environment Setup"

        def on_selection_list_selection_toggled(
            self, event: SelectionList.SelectionToggled
        ) -> None:
            sid = event.selection.value
            sl: SelectionList = self.query_one("#menu")

            # --- parent toggled: mirror state to all children ---
            if sid in parent_ids:
                new_state = sid in sl.selected
                children = [i for i in items if i.parent == sid]
                for child in children:
                    if new_state and child.id not in sl.selected:
                        sl.select(child.id)
                    elif not new_state and child.id in sl.selected:
                        sl.deselect(child.id)

            # --- child toggled on: ensure parent is selected ---
            if sid in child_ids:
                item = next(i for i in items if i.id == sid)
                if sid in sl.selected and item.parent not in sl.selected:
                    sl.select(item.parent)

            # Sync user_selected from widget state
            self._user_selected = set(sl.selected)

            # --- prerequisite auto-activation ---
            resolved = resolve_selection(items, self._user_selected)
            for rid in resolved - self._user_selected:
                if rid not in sl.selected:
                    sl.select(rid)
            for rid in (set(all_ids) - resolved):
                if rid in sl.selected and rid not in self._user_selected:
                    sl.deselect(rid)

        def action_confirm(self) -> None:
            sl: SelectionList = self.query_one("#menu")
            self._result = set(sl.selected)
            self.exit()

        def action_quit_abort(self) -> None:
            self._result = None
            self.exit()

        def action_cursor_down(self) -> None:
            self.query_one("#menu", SelectionList).action_cursor_down()

        def action_cursor_up(self) -> None:
            self.query_one("#menu", SelectionList).action_cursor_up()

    app = InstallerApp()
    app.run()
    return app._result


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

def _parse_args(items: list[InstallItem]) -> set[str] | None:
    """Parse CLI arguments and return the user_selected set (as canonical ids).

    Returns None if the TUI should be launched (no flag given, stdin is a TTY).
    Exits with an error if no flag is given and stdin is not a TTY.
    """
    all_ids = {item.id for item in items}
    name_to_id = {item.id: item.id for item in items}
    name_to_id |= {item.short_name: item.id for item in items}
    valid_names = ", ".join(sorted(name_to_id))

    parser = argparse.ArgumentParser(
        description="Dev environment installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l", "--list", dest="list", action="store_true",
        help="list available items and exit",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", dest="all", action="store_true",
        help="install everything without showing the menu",
    )
    group.add_argument(
        "--only", nargs="+", metavar="ITEM",
        help=f"install only the listed items (valid: {valid_names})",
    )
    group.add_argument(
        "--skip", nargs="+", metavar="ITEM",
        help=f"install everything except the listed items (valid: {valid_names})",
    )
    args = parser.parse_args()

    if args.list:
        _print_item_list(items)
        sys.exit(0)

    def _validate(names):
        unknown = set(names) - name_to_id.keys()
        if unknown:
            parser.error(f"unknown item(s): {', '.join(sorted(unknown))}. Valid: {valid_names}")

    def _resolve(names) -> set[str]:
        return {name_to_id[n] for n in names}

    if args.all:
        return all_ids
    if args.only:
        _validate(args.only)
        return _resolve(args.only)
    if args.skip:
        _validate(args.skip)
        return all_ids - _resolve(args.skip)

    # No flag given
    if not sys.stdin.isatty():
        print(
            "Error: no TTY detected and no selection flag given.\n"
            "Rerun with one of: --all, --only <item> [...], --skip <item> [...]",
            file=sys.stderr,
        )
        sys.exit(1)

    return None  # signal: launch TUI


def _print_item_list(items: list[InstallItem]) -> None:
    id_w = max(len(item.id) for item in items)
    sn_w = max(len(item.short_name) for item in items if item.short_name != item.id) or 0
    print(f"{'ID':<{id_w}}  {'SHORT NAME':<{sn_w}}  DESCRIPTION")
    print(f"{'-' * id_w}  {'-' * sn_w}  -----------")
    for item in items:
        sn = item.short_name if item.short_name != item.id else ""
        print(f"{item.id:<{id_w}}  {sn:<{sn_w}}  {item.description}")


def main():
    global _logfile

    items = _items()
    user_selected = _parse_args(items)

    if user_selected is None:
        user_selected = run_selection_menu(items)
        if user_selected is None:
            print("Aborted.")
            sys.exit(0)

    selected = resolve_selection(items, user_selected)

    _logfile = open(SCRIPT_DIR / "install.log", "w")

    with task("Dev environment setup"):
        init_password()

        with task("apt update"):
            sudo("DEBIAN_FRONTEND=noninteractive apt-get update -qq")

        install(items, selected)

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
    if not os.environ.get("VIRTUAL_ENV"):
        print("Error: no virtual environment detected. Run this script via './install.py' (requires uv), or activate a virtual environment first.")
        sys.exit(100)
    main()
