# Design: Fix Incus Init Already-Configured Check
**Status: Approved**

## Approach
Add a `sudo_ok(cmd) -> bool` helper that mirrors `sudo()` but returns `True`/`False`
instead of exiting on failure. Use it in `init_incus()` to replace the bare
`subprocess.run` check.

## Tasks
1. Add `sudo_ok(cmd) -> bool` helper alongside `sudo()`
2. Replace the bare `subprocess.run("incus storage show default", ...)` check in
   `init_incus()` with `sudo_ok("incus storage show default")`
3. Run unit tests
4. Confirm implementation complete and ready to archive
