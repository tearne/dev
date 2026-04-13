# Git User Config

## Intent
There is no installer option to configure a user's git identity or pull behaviour. On a fresh system, `user.name`, `user.email`, and the pull strategy (`merge` rather than `rebase`) are left unset, causing git to prompt or warn on first use. The installer should offer to set these, pre-selected when any are missing, and prompt for name and email at the start of the run when they are needed — making clear these are for git configuration only.

## Approach
Add two items under `[Git]`:

- **`git`** (apt): `install_check="git"`, `uses_sudo=True`. Makes the dependency explicit for completeness.
- **`git-config`**: `requires=["git"]`. `install_check` returns true only when all three settings — `user.name`, `user.email`, `pull.rebase` — are already set in global git config. `default_selected` is True when any are absent.

`install_git_config()` sets only the missing values: `user.name`, `user.email` via `git config --global`, and `pull.rebase false`.

If `git-config` is selected at the start of the run and `user.name` or `user.email` are unset, the installer prompts for them before the menu is shown — with a message that these are for git configuration only. The collected values are held in memory and passed to the install step.

No versioning applies. Review at end.

SPEC updates: add `git` and `git-config` to tools tree under `[Git]`; add `git` to the apt constraints list; document the prompt behaviour.

## Plan
- [x] ADD `install.py`: `install_git()` function (apt, consistent with other apt items)
- [x] ADD `install.py`: `install_git_config()` function — sets only missing values for `user.name`, `user.email`, and `pull.rebase false`
- [x] ADD `install.py`: `git_config_install_check()` helper — returns True when all three settings are present in global git config
- [x] ADD `install.py`: `InstallItem` for `git` under `[Git]` group, `install_check="git"`, `uses_sudo=True`
- [x] ADD `install.py`: `InstallItem` for `git-config` under `[Git]` group, `requires=["git"]`, using `git_config_install_check`, `default_selected` computed from missing settings
- [x] ADD `install.py`: pre-menu prompt for `user.name` and `user.email` when `git-config` is selected and either is unset — message must state these are for git configuration only
- [x] UPDATE `SPEC.md`: add `git` and `git-config` to the tools tree under `[Git]`; add `git` to the apt constraints list; document the prompt behaviour

## Conclusion
Delivered as planned. Added `import shlex` and `_git_user_name`/`_git_user_email` module globals to support the new functions. `git_config_setting()` placed in the utilities section as a reusable subprocess helper. Pre-menu prompt implemented as `collect_git_user_info()`, called from `main()` immediately after `_parse_args()`.
