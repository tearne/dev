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
    """Redirect HOME to tmp_path and reset module globals before each test."""
    monkeypatch.setenv("HOME", str(tmp_path))
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


def test_external_script_does_not_overwrite_real_file(tmp_path, monkeypatch):
    _make_cache(tmp_path, "tok", SHA)
    _stub_git_sha(monkeypatch, SHA)
    dst = tmp_path / ".local" / "bin" / "tok"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("existing content")
    install.install_external_script("https://example.com/tok.git", SHA, "tok.py", "tok")
    assert dst.read_text() == "existing content"
    assert len(install._warnings) == 1


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

def test_setup_local_bin_path_appends_to_profile(tmp_path):
    install.setup_local_bin_path()
    profile = tmp_path / ".profile"
    assert profile.exists()
    assert 'PATH="$HOME/.local/bin:$PATH"' in profile.read_text()


def test_setup_local_bin_path_skips_if_already_present(tmp_path):
    install.setup_local_bin_path()
    content_after_first = (tmp_path / ".profile").read_text()
    install.setup_local_bin_path()
    content_after_second = (tmp_path / ".profile").read_text()
    assert content_after_first == content_after_second


if __name__ == "__main__":
    if "pytest" not in sys.modules or "pytest.pytest_source" not in dir():
        sys.exit(pytest.main([__file__, "-v"]))
