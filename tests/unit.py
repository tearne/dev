#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# dependencies = ["pytest", "rich"]
# ///
"""Unit tests for install.py — file-operation logic only. No container required."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("VIRTUAL_ENV", "1")

import pytest
import install


@pytest.fixture(autouse=True)
def reset_install_state(tmp_path, monkeypatch):
    """Redirect HOME and TMPDIR to tmp_path and reset module globals before each test."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    install._warnings.clear()
    install._indent = 0


# ---------------------------------------------------------------------------
# _config_diff
# ---------------------------------------------------------------------------

def test_config_diff_equivalent(tmp_path):
    a = tmp_path / "a.toml"
    b = tmp_path / "b.toml"
    a.write_text("key = 'value'\n")
    b.write_text("key = 'value'  \n")  # trailing space — whitespace-equivalent
    assert install._config_diff(a, b) is None


def test_config_diff_different(tmp_path):
    a = tmp_path / "a.toml"
    b = tmp_path / "b.toml"
    a.write_text("key = 'value'\n")
    b.write_text("key = 'other'\n")
    assert install._config_diff(a, b) is not None


# ---------------------------------------------------------------------------
# _link_helix_config
# ---------------------------------------------------------------------------

def test_helix_config_creates_symlinks(tmp_path):
    install._link_helix_config()
    for filename in ("config.toml", "languages.toml"):
        dst = tmp_path / ".config" / "helix" / filename
        assert dst.is_symlink() and dst.exists()


def test_helix_config_skips_correct_symlink(tmp_path):
    install._link_helix_config()
    install._link_helix_config()  # second call — already correct
    assert len(install._warnings) == 0


def test_helix_config_replaces_dangling_symlink(tmp_path):
    dst = tmp_path / ".config" / "helix" / "config.toml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to("/nonexistent/path")
    assert not dst.exists()  # confirm dangling
    install._link_helix_config()
    assert dst.is_symlink() and dst.exists()


def test_helix_config_does_not_overwrite_different_real_file(tmp_path):
    dst = tmp_path / ".config" / "helix" / "config.toml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("theme = 'catppuccin'\n")
    install._link_helix_config()
    assert dst.read_text() == "theme = 'catppuccin'\n"
    assert any("not overwriting" in msg for msg, _ in install._warnings)


def test_helix_config_skips_equivalent_real_file(tmp_path):
    src = install.SCRIPT_DIR / "resources" / "helix" / "config.toml"
    dst = tmp_path / ".config" / "helix" / "config.toml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text())
    install._link_helix_config()
    assert not dst.is_symlink()  # left as a regular file
    assert len(install._warnings) == 0


# ---------------------------------------------------------------------------
# install_external_script
# ---------------------------------------------------------------------------

def _make_cache(tmp_path, name, sha):
    """Create a pre-populated cache directory simulating a fetched external script."""
    cache_dir = tmp_path / ".local" / "share" / "dev-installer" / "external" / name / sha
    cache_dir.mkdir(parents=True)
    script = cache_dir / f"{name}.py"
    script.write_text("#!/usr/bin/env python3\n")
    script.chmod(0o755)
    return cache_dir


def _stub_git_sha(monkeypatch, sha):
    """Make subprocess.run return the given sha for git rev-parse HEAD calls."""
    import subprocess as sp
    real_run = sp.run
    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd:
            return sp.CompletedProcess(cmd, 0, stdout=sha + "\n", stderr="")
        return real_run(cmd, **kwargs)
    monkeypatch.setattr(sp, "run", fake_run)


SHA = "a" * 40


def test_external_script_creates_symlink(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    dst = tmp_path / ".local" / "bin" / "tok"
    assert dst.is_symlink() and dst.exists()


def test_external_script_skips_fetch_when_cache_exists(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    run_calls = []
    monkeypatch.setattr(install, "run", lambda cmd: run_calls.append(cmd))
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert not any("fetch" in c for c in run_calls)


def test_external_script_skips_correct_symlink(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert len(install._warnings) == 0


def test_external_script_replaces_dangling_symlink(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    dst = tmp_path / ".local" / "bin" / "tok"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to("/nonexistent/tok")
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert dst.is_symlink() and dst.exists()


def test_external_script_replaces_installer_managed_symlink(tmp_path, monkeypatch):
    old_sha = "b" * 40
    new_sha = SHA
    _make_cache(tmp_path, "tok", old_sha)
    _make_cache(tmp_path, "tok", new_sha)
    _stub_git_sha(monkeypatch, new_sha)
    dst = tmp_path / ".local" / "bin" / "tok"
    dst.parent.mkdir(parents=True, exist_ok=True)
    old_src = tmp_path / ".local" / "share" / "dev-installer" / "external" / "tok" / old_sha / "tok.py"
    dst.symlink_to(old_src)
    install.install_external_script("https://example.com/tok.git", new_sha, "tok.py", "tok")
    assert dst.is_symlink() and dst.exists()
    assert str(new_sha) in str(dst.resolve())
    assert len(install._warnings) == 0


def test_external_script_replaces_unrelated_symlink(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    dst = tmp_path / ".local" / "bin" / "tok"
    dst.parent.mkdir(parents=True, exist_ok=True)
    elsewhere = tmp_path / "other" / "tok"
    elsewhere.parent.mkdir(parents=True, exist_ok=True)
    elsewhere.write_text("unrelated")
    dst.symlink_to(elsewhere)
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert dst.is_symlink()
    assert dst.resolve() != elsewhere.resolve()
    assert len(install._warnings) == 0


def test_external_script_replaces_real_file(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    dst = tmp_path / ".local" / "bin" / "tok"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("existing content")
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert dst.is_symlink()
    assert len(install._warnings) == 0


def test_external_script_aborts_on_sha_mismatch(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, "b" * 40)  # wrong SHA returned by git
    with pytest.raises(SystemExit):
        install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")


# ---------------------------------------------------------------------------
# resolve_selection
# ---------------------------------------------------------------------------

def _make_items():
    """Minimal item registry for selection tests:
      a (no requires)
      b (requires a)
      c (requires a)
      d (no requires)
    """
    noop = lambda: None
    return [
        install.InstallItem("a", noop),
        install.InstallItem("b", noop, requires=["a"]),
        install.InstallItem("c", noop, requires=["a"]),
        install.InstallItem("d", noop),
    ]


def test_resolve_activates_prerequisite():
    items = _make_items()
    selected = install.resolve_selection(items, {"b"})
    assert "a" in selected


def test_resolve_user_selected_item_kept():
    items = _make_items()
    selected = install.resolve_selection(items, {"b"})
    assert "b" in selected


def test_resolve_unrelated_item_excluded():
    items = _make_items()
    selected = install.resolve_selection(items, {"b"})
    assert "d" not in selected


def test_resolve_deselect_drops_auto_prerequisite():
    # b was selected (auto-activating a); deselecting b removes a
    items = _make_items()
    selected = install.resolve_selection(items, set())
    assert "a" not in selected
    assert "b" not in selected


def test_resolve_shared_prerequisite_kept_while_one_dependent_remains():
    # b and c both require a; deselecting b (only c remains) keeps a
    items = _make_items()
    selected = install.resolve_selection(items, {"c"})
    assert "a" in selected


def test_resolve_prerequisite_kept_when_independently_selected():
    # user explicitly selected both a and b; deselecting b (user_selected={"a"}) keeps a
    items = _make_items()
    selected = install.resolve_selection(items, {"a"})
    assert "a" in selected
    assert "b" not in selected


def test_resolve_all_items_selected_by_default():
    items = _make_items()
    all_ids = {item.id for item in items}
    selected = install.resolve_selection(items, all_ids)
    assert selected == all_ids


def test_resolve_only_flag_subset():
    items = _make_items()
    # --only d: no prerequisites needed
    selected = install.resolve_selection(items, {"d"})
    assert selected == {"d"}


def test_resolve_skip_flag_subset():
    items = _make_items()
    all_ids = {item.id for item in items}
    # --skip b,c: remove b and c from user_selected; a no longer required
    user_selected = all_ids - {"b", "c"}
    selected = install.resolve_selection(items, user_selected)
    assert "b" not in selected
    assert "c" not in selected
    assert "a" in selected   # a is still user-selected independently
    assert "d" in selected


def test_resolve_skip_removes_prerequisite_when_no_longer_needed():
    items = _make_items()
    # --skip a,b,c: none require anything; a,b,c all gone
    user_selected = {"d"}
    selected = install.resolve_selection(items, user_selected)
    assert selected == {"d"}


# ---------------------------------------------------------------------------
# InstallItem
# ---------------------------------------------------------------------------

def test_parent_defaults_to_none():
    item = install.InstallItem("my-item", lambda: None)
    assert item.parent is None


def test_parent_field_alone_does_not_add_install_dependency():
    # parent is visual-only; install deps require explicit requires=
    noop = lambda: None
    items = [
        install.InstallItem("parent-item", noop),
        install.InstallItem("child-item", noop, parent="parent-item"),
    ]
    selected = install.resolve_selection(items, {"child-item"})
    assert "parent-item" not in selected


def test_resolve_transitive_requires():
    # c requires b; b requires a — selecting c pulls in both
    noop = lambda: None
    items = [
        install.InstallItem("a", noop),
        install.InstallItem("b", noop, requires=["a"]),
        install.InstallItem("c", noop, requires=["b"]),
    ]
    selected = install.resolve_selection(items, {"c"})
    assert "a" in selected
    assert "b" in selected
    assert "c" in selected


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------

def _named_items():
    noop = lambda: None
    return [
        install.InstallItem("long-name", noop),
        install.InstallItem("other", noop),
    ]


def test_parse_args_only_accepts_full_id(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["install.py", "--only", "long-name"])
    result = install._parse_args(_named_items())
    assert result == {"long-name"}


def test_parse_args_rejects_unknown_name(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["install.py", "--only", "unknown"])
    with pytest.raises(SystemExit):
        install._parse_args(_named_items())


def test_parse_args_list_exits(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["install.py", "--list"])
    with pytest.raises(SystemExit) as exc:
        install._parse_args(_named_items())
    assert exc.value.code == 0


def test_parse_args_list_output(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["install.py", "--list"])
    with pytest.raises(SystemExit):
        install._parse_args(_named_items())
    out = capsys.readouterr().out
    assert "long-name" in out


def test_parse_args_list_shows_id(monkeypatch, capsys):
    noop = lambda: None
    items = [install.InstallItem("foo", noop)]
    monkeypatch.setattr(sys, "argv", ["install.py", "--list"])
    with pytest.raises(SystemExit):
        install._parse_args(items)
    out = capsys.readouterr().out
    assert "foo" in out


def test_parse_args_all_returns_all_ids(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["install.py", "--all"])
    result = install._parse_args(_named_items())
    assert result == {"long-name", "other"}


# ---------------------------------------------------------------------------
# _collect_descendants / _collect_ancestors
# ---------------------------------------------------------------------------

def _simple_tree():
    """
    Build children_of, parent_of, group_names for:
      [G]
        a
        [H]
          b
    """
    children_of = {
        None:  [("G", True)],
        "G":   [("a", False), ("H", True)],
        "H":   [("b", False)],
    }
    parent_of = {"G": None, "a": "G", "H": "G", "b": "H"}
    group_names = {"G", "H"}
    return children_of, parent_of, group_names


def test_collect_descendants_leaf_returns_empty():
    children_of, parent_of, group_names = _simple_tree()
    assert install._collect_descendants("b", children_of) == []


def test_collect_descendants_item_with_no_children():
    children_of, parent_of, group_names = _simple_tree()
    assert install._collect_descendants("a", children_of) == []


def test_collect_descendants_group_includes_direct_children():
    children_of, parent_of, group_names = _simple_tree()
    result = install._collect_descendants("H", children_of)
    assert "b" in result


def test_collect_descendants_recurses_into_subgroups():
    children_of, parent_of, group_names = _simple_tree()
    result = install._collect_descendants("G", children_of)
    assert "a" in result
    assert "__group_H__" in result
    assert "b" in result


def test_collect_ancestors_root_returns_empty():
    children_of, parent_of, group_names = _simple_tree()
    assert install._collect_ancestors("G", parent_of, group_names) == []


def test_collect_ancestors_direct_child_of_group():
    children_of, parent_of, group_names = _simple_tree()
    result = install._collect_ancestors("a", parent_of, group_names)
    assert result == ["__group_G__"]


def test_collect_ancestors_deeply_nested():
    children_of, parent_of, group_names = _simple_tree()
    result = install._collect_ancestors("b", parent_of, group_names)
    assert result == ["__group_H__", "__group_G__"]


# ---------------------------------------------------------------------------
# detect_session_type
# ---------------------------------------------------------------------------

def test_detect_session_type_wayland_display(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    assert install.detect_session_type() == "wayland"


def test_detect_session_type_xdg_wayland(monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert install.detect_session_type() == "wayland"


def test_detect_session_type_x11(monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert install.detect_session_type() == "x11"


def test_detect_session_type_headless(monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    assert install.detect_session_type() is None


# ---------------------------------------------------------------------------
# InstallItem default_selected
# ---------------------------------------------------------------------------

def test_default_selected_defaults_to_true():
    item = install.InstallItem("x", lambda: None)
    assert item.default_selected is True



# ---------------------------------------------------------------------------
# install_rust PATH update
# ---------------------------------------------------------------------------

def test_install_rust_updates_path_when_already_installed(tmp_path, monkeypatch):
    # Simulate rust already installed; subprocess calls are no-ops
    monkeypatch.setattr(install, "is_installed", lambda cmd: True)
    monkeypatch.setattr(install, "sudo", lambda cmd: None)
    monkeypatch.setattr(install, "run", lambda cmd: None)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")  # cargo bin absent

    install.install_rust()

    cargo_bin = str(tmp_path / ".cargo" / "bin")
    assert cargo_bin in os.environ["PATH"]


# ---------------------------------------------------------------------------
# setup_local_bin_path
# ---------------------------------------------------------------------------

def test_setup_local_bin_path_appends_to_profile_and_bashrc(tmp_path):
    install.setup_local_bin_path()
    for name in (".profile", ".bashrc"):
        f = tmp_path / name
        assert f.exists()
        assert 'PATH="$HOME/.local/bin:$PATH"' in f.read_text()


def test_setup_local_bin_path_skips_if_already_present(tmp_path):
    install.setup_local_bin_path()
    contents_after_first = {n: (tmp_path / n).read_text() for n in (".profile", ".bashrc")}
    install.setup_local_bin_path()
    for name, content in contents_after_first.items():
        assert (tmp_path / name).read_text() == content


# ---------------------------------------------------------------------------
# setup_helix_as_editor
# ---------------------------------------------------------------------------

def test_setup_helix_as_editor_appends_to_profile_and_bashrc(tmp_path):
    install.setup_helix_as_editor()
    for name in (".profile", ".bashrc"):
        f = tmp_path / name
        assert f.exists()
        assert "export EDITOR=hx" in f.read_text()


def test_setup_helix_as_editor_skips_if_already_present(tmp_path):
    install.setup_helix_as_editor()
    contents_after_first = {n: (tmp_path / n).read_text() for n in (".profile", ".bashrc")}
    install.setup_helix_as_editor()
    for name, content in contents_after_first.items():
        assert (tmp_path / name).read_text() == content


def test_setup_helix_as_editor_skips_file_with_existing_editor_config(tmp_path):
    (tmp_path / ".bashrc").write_text("export EDITOR=vim\n")
    install.setup_helix_as_editor()
    assert "EDITOR=hx" not in (tmp_path / ".bashrc").read_text()
    assert "export EDITOR=hx" in (tmp_path / ".profile").read_text()


# ---------------------------------------------------------------------------
# configure callback
# ---------------------------------------------------------------------------

def test_configure_called_for_installed_item_after_install_loop(tmp_path):
    called = []
    noop = lambda: None
    item = install.InstallItem("present", noop, install_check=lambda: True, configure=lambda: called.append("present"))
    install.install([item], set())
    assert "present" in called


def test_configure_not_called_when_install_check_fails(tmp_path):
    called = []
    noop = lambda: None
    item = install.InstallItem("absent", noop, install_check=lambda: False, configure=lambda: called.append("absent"))
    install.install([item], set())
    assert called == []


def test_configure_not_called_when_no_configure_set(tmp_path):
    noop = lambda: None
    item = install.InstallItem("present", noop, install_check=lambda: True)
    install.install([item], set())  # should not raise


# ---------------------------------------------------------------------------
# needs_sudo
# ---------------------------------------------------------------------------

def test_needs_sudo_true_when_selected_item_uses_sudo():
    noop = lambda: None
    items = [
        install.InstallItem("a", noop, uses_sudo=True),
        install.InstallItem("b", noop, uses_sudo=False),
    ]
    assert install.needs_sudo(items, {"a"}) is True


def test_needs_sudo_false_when_no_selected_item_uses_sudo():
    noop = lambda: None
    items = [
        install.InstallItem("a", noop, uses_sudo=True),
        install.InstallItem("b", noop, uses_sudo=False),
    ]
    assert install.needs_sudo(items, {"b"}) is False


def test_needs_sudo_false_for_empty_selection():
    noop = lambda: None
    items = [install.InstallItem("a", noop, uses_sudo=True)]
    assert install.needs_sudo(items, set()) is False


def test_needs_sudo_false_when_sudo_item_not_selected():
    noop = lambda: None
    items = [
        install.InstallItem("a", noop, uses_sudo=True),
        install.InstallItem("b", noop, uses_sudo=False),
    ]
    assert install.needs_sudo(items, {"b"}) is False


def test_needs_sudo_false_when_sudo_item_already_installed():
    noop = lambda: None
    items = [install.InstallItem("a", noop, uses_sudo=True, install_check=lambda: True)]
    assert install.needs_sudo(items, {"a"}) is False


def test_needs_sudo_true_when_sudo_item_not_yet_installed():
    noop = lambda: None
    items = [install.InstallItem("a", noop, uses_sudo=True, install_check=lambda: False)]
    assert install.needs_sudo(items, {"a"}) is True


# ---------------------------------------------------------------------------
# in_container
# ---------------------------------------------------------------------------

def _fake_run_factory(returncode):
    """Return a subprocess.run replacement that always returns the given code."""
    import subprocess as sp
    def fake_run(cmd, **kwargs):
        return sp.CompletedProcess(cmd, returncode)
    return fake_run


def test_in_container_true_via_systemd_detect_virt(monkeypatch):
    monkeypatch.setattr("subprocess.run", _fake_run_factory(0))
    assert install.in_container() is True


def test_in_container_false_via_systemd_detect_virt(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.run", _fake_run_factory(1))
    monkeypatch.setattr(install, "_CONTAINER_MARKER_FILES", ())
    assert install.in_container() is False


def test_in_container_fallback_marker_file(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.run", _fake_run_factory(1))
    marker = tmp_path / ".containerenv"
    marker.touch()
    monkeypatch.setattr(install, "_CONTAINER_MARKER_FILES", (marker,))
    assert install.in_container() is True


def test_in_container_fallback_no_marker_files(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.run", _fake_run_factory(1))
    monkeypatch.setattr(install, "_CONTAINER_MARKER_FILES", (tmp_path / "absent",))
    assert install.in_container() is False


def test_in_container_systemd_absent_falls_back_to_marker(monkeypatch, tmp_path):
    """Exit 127 (command not found via shell) falls back to marker files."""
    monkeypatch.setattr("subprocess.run", _fake_run_factory(127))
    marker = tmp_path / ".containerenv"
    marker.touch()
    monkeypatch.setattr(install, "_CONTAINER_MARKER_FILES", (marker,))
    assert install.in_container() is True


# ---------------------------------------------------------------------------
# compute_item_hints
# ---------------------------------------------------------------------------

def _hint_items():
    noop = lambda: None
    return [
        install.InstallItem("plain",   noop, install_check=None),
        install.InstallItem("present", noop, install_check=lambda: True),
        install.InstallItem("absent",  noop, install_check=lambda: False),
        install.InstallItem("incus",   noop, install_check=lambda: False),
        install.InstallItem("preoff",  noop, install_check=None, default_selected=False),
    ]


def test_compute_hints_installed_item_deselected(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: False)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["present"]
    assert selected is False
    assert hint == "installed"


def test_compute_hints_absent_item_selected(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: False)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["absent"]
    assert selected is True
    assert hint is None


def test_compute_hints_no_check_preserves_default_selected(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: False)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["plain"]
    assert selected is True
    assert hint is None


def test_compute_hints_no_check_preserves_default_selected_false(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: False)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["preoff"]
    assert selected is False
    assert hint is None


def test_compute_hints_incus_in_container_deselected(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: True)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["incus"]
    assert selected is False
    assert hint == "already in container"


def test_compute_hints_incus_not_in_container_unaffected(monkeypatch):
    monkeypatch.setattr(install, "in_container", lambda: False)
    hints = install.compute_item_hints(_hint_items())
    selected, hint = hints["incus"]
    assert selected is True   # install_check returns False → not installed → keep selected
    assert hint is None


# ---------------------------------------------------------------------------
# head_state_label
# ---------------------------------------------------------------------------

def test_head_state_label_pending_shows_spinner():
    label = install.head_state_label(install.Pending(frame=0))
    assert install._SPINNER[0] in label

def test_head_state_label_pending_advances_frame():
    label0 = install.head_state_label(install.Pending(frame=0))
    label1 = install.head_state_label(install.Pending(frame=1))
    assert label0 != label1

def test_head_state_label_at_head_contains_label_head_and_tick():
    label = install.head_state_label(install.AtHead(label="ext a1b2c3d"))
    assert "ext a1b2c3d" in label
    assert "HEAD" in label
    assert "✓" in label
    assert "green" in label

def test_head_state_label_behind_contains_label_update_hint_and_question_mark():
    label = install.head_state_label(install.Behind(label="ext a1b2c3d"))
    assert "ext a1b2c3d" in label
    assert "HEAD" not in label
    assert "update available" in label
    assert "?" in label
    assert "yellow" in label

def test_head_state_label_check_failed_shows_question_mark():
    label = install.head_state_label(install.CheckFailed())
    assert "?" in label


# ---------------------------------------------------------------------------
# check_remote_head
# ---------------------------------------------------------------------------

def TEST_check_remote_head_returns_at_head_when_shas_match(monkeypatch):
    sha = "a" * 40
    monkeypatch.setattr(install.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": f"{sha}\tHEAD\n"})())
    result = install.check_remote_head("https://example.com/repo.git", sha)
    assert isinstance(result, install.AtHead)
    assert result.label == f"ext {sha[:7]}"

def TEST_check_remote_head_returns_behind_when_shas_differ(monkeypatch):
    pinned = "a" * 40
    remote = "b" * 40
    monkeypatch.setattr(install.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": f"{remote}\tHEAD\n"})())
    result = install.check_remote_head("https://example.com/repo.git", pinned)
    assert isinstance(result, install.Behind)
    assert result.label == f"ext {pinned[:7]}"

def TEST_check_remote_head_returns_failed_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 1, "stdout": ""})())
    result = install.check_remote_head("https://example.com/repo.git", "a" * 40)
    assert isinstance(result, install.CheckFailed)

def TEST_check_remote_head_returns_failed_on_empty_output(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": ""})())
    result = install.check_remote_head("https://example.com/repo.git", "a" * 40)
    assert isinstance(result, install.CheckFailed)


# ---------------------------------------------------------------------------
# external install_check (symlink verification)
# ---------------------------------------------------------------------------

def TEST_external_install_check_true_when_symlink_points_into_cache(tmp_path):
    sha = "abc123"
    cache_dir = tmp_path / ".local" / "share" / "dev-installer" / "external" / "tok" / sha
    cache_dir.mkdir(parents=True)
    target = cache_dir / "tok.py"
    target.touch()
    bin_path = tmp_path / ".local" / "bin" / "tok"
    bin_path.parent.mkdir(parents=True)
    bin_path.symlink_to(target)
    check = lambda b=bin_path, d=cache_dir: b.is_symlink() and b.resolve().is_relative_to(d)
    assert check() is True

def TEST_external_install_check_false_when_symlink_points_to_different_sha(tmp_path):
    old_cache = tmp_path / ".local" / "share" / "dev-installer" / "external" / "tok" / "oldsha"
    new_cache = tmp_path / ".local" / "share" / "dev-installer" / "external" / "tok" / "newsha"
    old_cache.mkdir(parents=True)
    new_cache.mkdir(parents=True)
    target = old_cache / "tok.py"
    target.touch()
    bin_path = tmp_path / ".local" / "bin" / "tok"
    bin_path.parent.mkdir(parents=True)
    bin_path.symlink_to(target)
    check = lambda b=bin_path, d=new_cache: b.is_symlink() and b.resolve().is_relative_to(d)
    assert check() is False

def TEST_external_install_check_false_when_not_installed(tmp_path):
    cache_dir = tmp_path / ".local" / "share" / "dev-installer" / "external" / "tok" / "abc123"
    bin_path  = tmp_path / ".local" / "bin" / "tok"
    check = lambda b=bin_path, d=cache_dir: b.is_symlink() and b.resolve().is_relative_to(d)
    assert check() is False


# ---------------------------------------------------------------------------
# Tarball release installs
# ---------------------------------------------------------------------------

import io
import re as _re
import shutil as _shutil
import subprocess as _sp
import tarfile as _tarfile


def _make_test_tarball(path: Path, top_dir: str, binary_name: str) -> None:
    """Build a minimal tar.xz with structure: top_dir/binary_name (executable)."""
    content = b"#!/bin/sh\necho ok\n"
    with _tarfile.open(path, "w:xz") as tf:
        d = _tarfile.TarInfo(top_dir)
        d.type = _tarfile.DIRTYPE
        d.mode = 0o755
        tf.addfile(d)
        b = _tarfile.TarInfo(f"{top_dir}/{binary_name}")
        b.size = len(content)
        b.mode = 0o755
        tf.addfile(b, io.BytesIO(content))


def _make_test_tarball_no_wrapper(path: Path, binary_name: str) -> None:
    """Build a minimal tar.xz with bin/<binary_name> and lib/dep.so at archive root (no wrapper dir)."""
    content = b"#!/bin/sh\necho ok\n"
    with _tarfile.open(path, "w:xz") as tf:
        for d in ("bin", "lib"):
            di = _tarfile.TarInfo(d)
            di.type = _tarfile.DIRTYPE
            di.mode = 0o755
            tf.addfile(di)
        b = _tarfile.TarInfo(f"bin/{binary_name}")
        b.size = len(content)
        b.mode = 0o755
        tf.addfile(b, io.BytesIO(content))
        lib = _tarfile.TarInfo("lib/dep.so")
        lib.size = len(content)
        lib.mode = 0o644
        tf.addfile(lib, io.BytesIO(content))


def _make_kitty_test_tarball(path: Path) -> None:
    """Build a minimal kitty-shaped tar.xz: bin/{kitty,kitten}, lib/dep.so, desktop file, icons — no wrapper dir."""
    content = b"#!/bin/sh\necho ok\n"
    with _tarfile.open(path, "w:xz") as tf:
        def add_dir(name):
            d = _tarfile.TarInfo(name)
            d.type = _tarfile.DIRTYPE
            d.mode = 0o755
            tf.addfile(d)

        def add_file(name, data=content, mode=0o755):
            f = _tarfile.TarInfo(name)
            f.size = len(data)
            f.mode = mode
            tf.addfile(f, io.BytesIO(data))

        for d in ("bin", "lib", "share/applications",
                  "share/icons/hicolor/256x256/apps", "share/icons/hicolor/scalable/apps"):
            add_dir(d)
        add_file("bin/kitty")
        add_file("bin/kitten")
        add_file("lib/dep.so", mode=0o644)
        add_file("share/applications/kitty.desktop", data=b"[Desktop Entry]\n", mode=0o644)
        add_file("share/icons/hicolor/256x256/apps/kitty.png", data=b"png", mode=0o644)
        add_file("share/icons/hicolor/scalable/apps/kitty.svg", data=b"svg", mode=0o644)


def _stub_release(monkeypatch, tmp_path: Path, repo: str, version: str, top_dir: str, binary: str,
                   build_archive=None, suffix: str = ".tar.xz") -> Path:
    """Stub the GitHub API + curl download so install_tarball_release runs without network.

    build_archive, if given, is called as build_archive(archive_path) instead of the default
    single-wrapper-dir builder — used to exercise the no-wrapper extraction path.
    Returns the path of the prepared archive (also written by the fake `run`)."""
    archive_src = tmp_path / "_release_archive.tar.xz"
    if build_archive is None:
        _make_test_tarball(archive_src, top_dir, binary)
    else:
        build_archive(archive_src)
    api_json = (
        f'{{"tag_name": "{version}", '
        f'"assets": [{{"browser_download_url": "https://example.com/{top_dir}{suffix}"}}], '
        f'"browser_download_url": "https://example.com/{top_dir}{suffix}"}}'
    )
    real_run = _sp.run

    def fake_subprocess_run(cmd, **kwargs):
        if isinstance(cmd, str) and "api.github.com" in cmd and repo in cmd:
            return _sp.CompletedProcess(cmd, 0, stdout=api_json, stderr="")
        if isinstance(cmd, str) and "dpkg -l" in cmd:
            return _sp.CompletedProcess(cmd, 0, stdout="", stderr="")
        return real_run(cmd, **kwargs)
    monkeypatch.setattr(install.subprocess, "run", fake_subprocess_run)

    def fake_install_run(cmd):
        match = _re.search(r"-o\s+(\S+)", cmd)
        if match:
            _shutil.copy(archive_src, Path(match.group(1)))
    monkeypatch.setattr(install, "run", fake_install_run)
    return archive_src


# _tarball_state_dir / installed_tarball_version

def test_tarball_state_dir_under_home(tmp_path):
    assert install._tarball_state_dir("foo") == tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "foo"


def test_installed_tarball_version_returns_none_when_absent(tmp_path):
    assert install.installed_tarball_version("foo") is None


def test_installed_tarball_version_returns_none_when_state_dir_empty(tmp_path):
    install._tarball_state_dir("foo").mkdir(parents=True)
    assert install.installed_tarball_version("foo") is None


def test_installed_tarball_version_returns_version_when_one_dir(tmp_path):
    (install._tarball_state_dir("foo") / "1.2.3").mkdir(parents=True)
    assert install.installed_tarball_version("foo") == "1.2.3"


def test_installed_tarball_version_returns_lex_last_when_multiple_dirs(tmp_path):
    base = install._tarball_state_dir("foo")
    (base / "1.2.3").mkdir(parents=True)
    (base / "1.2.4").mkdir(parents=True)
    assert install.installed_tarball_version("foo") == "1.2.4"


# check_release_version

def _stub_release_api(monkeypatch, tag_name: str | None, returncode: int = 0, stdout_override: str | None = None):
    if stdout_override is not None:
        stdout = stdout_override
    elif tag_name is None:
        stdout = "{}"
    else:
        stdout = f'{{"tag_name": "{tag_name}"}}'
    monkeypatch.setattr(install.subprocess, "run",
        lambda *a, **kw: _sp.CompletedProcess(a[0], returncode, stdout=stdout, stderr=""))


def test_check_release_version_returns_failed_when_installed_is_none(monkeypatch):
    _stub_release_api(monkeypatch, "1.0.0")
    result = install.check_release_version("owner/repo", None)
    assert isinstance(result, install.CheckFailed)


def test_check_release_version_returns_at_head_when_versions_match(monkeypatch):
    _stub_release_api(monkeypatch, "1.0.0")
    result = install.check_release_version("owner/repo", "1.0.0")
    assert isinstance(result, install.AtHead)
    assert result.label == "1.0.0"


def test_check_release_version_returns_behind_with_version_pair_label(monkeypatch):
    _stub_release_api(monkeypatch, "1.0.1")
    result = install.check_release_version("owner/repo", "1.0.0")
    assert isinstance(result, install.Behind)
    assert "1.0.0" in result.label and "1.0.1" in result.label


def test_check_release_version_returns_failed_on_curl_nonzero(monkeypatch):
    _stub_release_api(monkeypatch, None, returncode=1, stdout_override="")
    result = install.check_release_version("owner/repo", "1.0.0")
    assert isinstance(result, install.CheckFailed)


def test_check_release_version_returns_failed_when_no_tag_name(monkeypatch):
    _stub_release_api(monkeypatch, None, stdout_override='{"name": "no tag"}')
    result = install.check_release_version("owner/repo", "1.0.0")
    assert isinstance(result, install.CheckFailed)


# _link_tarball_binary — regression test for the symlink-naming bug

def test_link_tarball_binary_uses_binary_name_not_arbitrary_name(tmp_path):
    target = tmp_path / "extracted"
    target.mkdir()
    (target / "hx").write_text("binary content")
    install._link_tarball_binary(target, "hx")
    assert (tmp_path / ".local" / "bin" / "hx").is_symlink()
    assert not (tmp_path / ".local" / "bin" / "helix").exists()


def test_link_tarball_binary_idempotent_when_correct(tmp_path):
    target = tmp_path / "extracted"
    target.mkdir()
    (target / "hx").write_text("binary")
    install._link_tarball_binary(target, "hx")
    install._link_tarball_binary(target, "hx")
    assert (tmp_path / ".local" / "bin" / "hx").is_symlink()


def test_link_tarball_binary_replaces_stale_symlink(tmp_path):
    target = tmp_path / "extracted"
    target.mkdir()
    (target / "hx").write_text("binary")
    bin_dir = tmp_path / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "hx").symlink_to("/nonexistent/path")
    install._link_tarball_binary(target, "hx")
    assert (bin_dir / "hx").resolve() == (target / "hx").resolve()


# _warn_if_dpkg_helix_present

def test_warn_if_dpkg_helix_present_silent_when_no_system_install(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run",
        lambda *a, **kw: _sp.CompletedProcess(a[0], 1, stdout="", stderr=""))
    install._warn_if_dpkg_helix_present()
    assert not install._warnings


def test_warn_if_dpkg_helix_present_warns_when_dpkg_lists_helix(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run",
        lambda *a, **kw: _sp.CompletedProcess(a[0], 0, stdout="helix\n", stderr=""))
    install._warn_if_dpkg_helix_present()
    assert install._warnings
    assert any("apt remove helix" in msg for msg, _diff in install._warnings)


# install_tarball_release end-to-end

def test_install_tarball_release_creates_state_dir_and_symlink(tmp_path, monkeypatch):
    top_dir = f"helix-25.07.1-{install.platform.machine()}-linux"
    _stub_release(monkeypatch, tmp_path, "helix-editor/helix", "25.07.1", top_dir, "hx")
    install.install_tarball_release(
        name="helix",
        repo="helix-editor/helix",
        asset_pattern="{arch}-linux.tar.xz",
        binary="hx",
    )
    state = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "helix" / "25.07.1"
    assert state.is_dir()
    assert (state / "hx").is_file()
    bin_link = tmp_path / ".local" / "bin" / "hx"
    assert bin_link.is_symlink()
    assert bin_link.resolve() == (state / "hx").resolve()


def test_install_tarball_release_no_op_when_already_at_latest(tmp_path, monkeypatch):
    top_dir = f"helix-25.07.1-{install.platform.machine()}-linux"
    _stub_release(monkeypatch, tmp_path, "helix-editor/helix", "25.07.1", top_dir, "hx")
    state = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "helix" / "25.07.1"
    state.mkdir(parents=True)
    (state / "hx").write_text("placeholder")

    run_calls = []
    real_run = install.run
    def tracking_run(cmd):
        run_calls.append(cmd)
        return real_run(cmd)
    monkeypatch.setattr(install, "run", tracking_run)

    install.install_tarball_release(
        name="helix",
        repo="helix-editor/helix",
        asset_pattern="{arch}-linux.tar.xz",
        binary="hx",
    )
    assert not any("curl" in c for c in run_calls)
    assert (state / "hx").read_text() == "placeholder"  # untouched


def test_install_tarball_release_replaces_prior_version(tmp_path, monkeypatch):
    top_dir = f"helix-25.07.1-{install.platform.machine()}-linux"
    _stub_release(monkeypatch, tmp_path, "helix-editor/helix", "25.07.1", top_dir, "hx")
    base = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "helix"
    old = base / "25.07.0"
    old.mkdir(parents=True)
    (old / "hx").write_text("old")

    install.install_tarball_release(
        name="helix",
        repo="helix-editor/helix",
        asset_pattern="{arch}-linux.tar.xz",
        binary="hx",
    )
    assert not old.exists()
    assert (base / "25.07.1" / "hx").is_file()


def test_install_tarball_release_does_not_touch_real_home(tmp_path, monkeypatch):
    """Belt-and-braces: every artefact lands strictly under tmp_path."""
    real_home = Path.home()
    assert real_home == tmp_path  # fixture invariant
    top_dir = f"helix-25.07.1-{install.platform.machine()}-linux"
    _stub_release(monkeypatch, tmp_path, "helix-editor/helix", "25.07.1", top_dir, "hx")
    install.install_tarball_release(
        name="helix",
        repo="helix-editor/helix",
        asset_pattern="{arch}-linux.tar.xz",
        binary="hx",
    )
    # Nothing leaked above tmp_path.
    assert all(p.is_relative_to(tmp_path) for p in [
        Path.home() / ".local" / "bin" / "hx",
        install._tarball_state_dir("helix"),
    ])


def test_install_tarball_release_substitutes_version_placeholder(tmp_path, monkeypatch):
    _stub_release(monkeypatch, tmp_path, "acme/tool", "v1.2.3", "tool-1.2.3", "tool")
    install.install_tarball_release(
        name="tool",
        repo="acme/tool",
        asset_pattern="{version}.tar.xz",
        binary="tool",
    )
    state = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "tool" / "v1.2.3"
    assert (state / "tool").is_file()


def test_install_tarball_release_extracts_archive_without_wrapper_directory(tmp_path, monkeypatch):
    _stub_release(
        monkeypatch, tmp_path, "acme/tool", "1.0.0", "tool-1.0.0", "tool",
        build_archive=lambda p: _make_test_tarball_no_wrapper(p, "tool"),
    )
    install.install_tarball_release(
        name="tool",
        repo="acme/tool",
        asset_pattern="{version}.tar.xz",
        binary="bin/tool",
    )
    state = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "tool" / "1.0.0"
    assert (state / "bin" / "tool").is_file()
    assert (state / "lib" / "dep.so").is_file()
    bin_link = tmp_path / ".local" / "bin" / "tool"
    assert bin_link.resolve() == (state / "bin" / "tool").resolve()


# _warn_if_dpkg_kitty_present

def test_warn_if_dpkg_kitty_present_silent_when_no_system_install(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run",
        lambda *a, **kw: _sp.CompletedProcess(a[0], 1, stdout="", stderr=""))
    install._warn_if_dpkg_kitty_present()
    assert not install._warnings


def test_warn_if_dpkg_kitty_present_warns_when_dpkg_lists_kitty(monkeypatch):
    monkeypatch.setattr(install.subprocess, "run",
        lambda *a, **kw: _sp.CompletedProcess(a[0], 0, stdout="kitty\n", stderr=""))
    install._warn_if_dpkg_kitty_present()
    assert install._warnings
    assert any("apt remove kitty" in msg for msg, _diff in install._warnings)


# _link_kitty_desktop_icon

def test_link_kitty_desktop_icon_noop_when_headless(tmp_path, monkeypatch):
    monkeypatch.setattr(install, "detect_session_type", lambda: None)
    target = tmp_path / "extracted"
    (target / "share" / "applications").mkdir(parents=True)
    (target / "share" / "applications" / "kitty.desktop").write_text("desktop entry")
    install._link_kitty_desktop_icon(target)
    assert not (tmp_path / ".local" / "share" / "applications" / "kitty.desktop").exists()


def test_link_kitty_desktop_icon_symlinks_when_graphical(tmp_path, monkeypatch):
    monkeypatch.setattr(install, "detect_session_type", lambda: "wayland")
    target = tmp_path / "extracted"
    (target / "share" / "applications").mkdir(parents=True)
    (target / "share" / "applications" / "kitty.desktop").write_text("desktop entry")
    (target / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)
    (target / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png").write_text("png")
    (target / "share" / "icons" / "hicolor" / "scalable" / "apps").mkdir(parents=True)
    (target / "share" / "icons" / "hicolor" / "scalable" / "apps" / "kitty.svg").write_text("svg")
    install._link_kitty_desktop_icon(target)
    desktop = tmp_path / ".local" / "share" / "applications" / "kitty.desktop"
    assert desktop.is_symlink()
    assert desktop.resolve() == (target / "share" / "applications" / "kitty.desktop").resolve()
    icon = tmp_path / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png"
    assert icon.is_symlink()


def test_link_kitty_desktop_icon_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(install, "detect_session_type", lambda: "x11")
    target = tmp_path / "extracted"
    (target / "share" / "applications").mkdir(parents=True)
    (target / "share" / "applications" / "kitty.desktop").write_text("desktop entry")
    (target / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)
    (target / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png").write_text("png")
    (target / "share" / "icons" / "hicolor" / "scalable" / "apps").mkdir(parents=True)
    (target / "share" / "icons" / "hicolor" / "scalable" / "apps" / "kitty.svg").write_text("svg")
    install._link_kitty_desktop_icon(target)
    install._link_kitty_desktop_icon(target)
    desktop = tmp_path / ".local" / "share" / "applications" / "kitty.desktop"
    assert desktop.is_symlink()


# install_kitty end-to-end

def test_install_kitty_installs_binaries_and_desktop_icon_when_graphical(tmp_path, monkeypatch):
    monkeypatch.setattr(install.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(install, "detect_session_type", lambda: "wayland")
    _stub_release(
        monkeypatch, tmp_path, "kovidgoyal/kitty", "v0.47.4", "kitty-0.47.4-x86_64", "bin/kitty",
        build_archive=_make_kitty_test_tarball, suffix=".txz",
    )
    install.install_kitty()

    state = tmp_path / ".local" / "share" / "dev-installer" / "tarball" / "kitty" / "v0.47.4"
    assert (state / "bin" / "kitty").is_file()
    assert (state / "bin" / "kitten").is_file()
    assert (tmp_path / ".local" / "bin" / "kitty").is_symlink()
    assert (tmp_path / ".local" / "bin" / "kitten").is_symlink()
    assert (tmp_path / ".local" / "share" / "applications" / "kitty.desktop").is_symlink()
    assert (tmp_path / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "kitty.png").is_symlink()


def test_install_kitty_skips_desktop_icon_when_headless(tmp_path, monkeypatch):
    monkeypatch.setattr(install.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(install, "detect_session_type", lambda: None)
    _stub_release(
        monkeypatch, tmp_path, "kovidgoyal/kitty", "v0.47.4", "kitty-0.47.4-x86_64", "bin/kitty",
        build_archive=_make_kitty_test_tarball, suffix=".txz",
    )
    install.install_kitty()

    assert (tmp_path / ".local" / "bin" / "kitty").is_symlink()
    assert not (tmp_path / ".local" / "share" / "applications" / "kitty.desktop").exists()


def test_install_kitty_resolves_arm64_asset_name_from_aarch64_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(install.platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(install, "detect_session_type", lambda: None)
    _stub_release(
        monkeypatch, tmp_path, "kovidgoyal/kitty", "v0.47.4", "kitty-0.47.4-arm64", "bin/kitty",
        build_archive=_make_kitty_test_tarball, suffix=".txz",
    )
    install.install_kitty()
    assert (tmp_path / ".local" / "bin" / "kitty").is_symlink()


if __name__ == "__main__":
    if "pytest" not in sys.modules or "pytest.pytest_source" not in dir():
        sys.exit(pytest.main([__file__, "-v"]))
