# Defer Git Identity Prompt

## Intent

The installer currently asks for `user.name` and `user.email` before the selection menu appears. This means the user is prompted for git identity even if they end up deselecting `git-config`, or before they've confirmed the installation should proceed. The prompt should only appear after the user has confirmed their final selection and only when that selection includes `git-config` with missing identity values.

## Approach

Move `collect_git_user_info()` from its current call site (before the menu, `main()` line 1273) to after both the TUI and CLI paths have produced a final `selected` set and the user has confirmed. Currently the function accepts `user_selected: set[str] | None` and branches on whether it's `None` (TUI) or not (CLI) — after the move, `selected` is always known, so simplify the signature to accept `selected: set[str]` directly and just check `"git-config" in selected`.

The SPEC section "Git Identity Prompt" (`SPEC.md` line 109–110) currently says the prompt happens "before the menu is shown". Update it to reflect the new timing: after selection is confirmed and before installation begins.

Review cadence: at the end.

## Plan

- [x] UPDATE `collect_git_user_info()` in `install.py` — change signature from `(items, user_selected)` to `(selected: set[str])`, remove the `user_selected is None` branch, and check `"git-config" in selected` directly
- [x] UPDATE `main()` in `install.py` — remove the call at line 1273 (before the menu), add the call after both TUI and CLI paths have finalised `selected` and the user has confirmed (just before the logfile/install block)
- [x] UPDATE SPEC `SPEC.md` line 109–110 — change "before the menu is shown" to reflect the new timing (after selection is confirmed, before installation begins)
- [x] REVIEW — run `python install.py --help` to confirm no syntax errors

## Conclusion

Completed as planned — no deviations or surprises.
