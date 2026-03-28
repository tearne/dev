# Helix System Editor
**Type**: Fix
**Status**: Approved

## Log

Set helix as the system editor via the EDITOR environment variable, so it is used for things like git commit messages. Appended to both ~/.profile (login shells) and ~/.bashrc (interactive non-login shells), each idempotently guarded.
