# Proposal: Fix Incus Init Already-Configured Check
**Status: Approved**

## Intent
The "already initialised" check in `init_incus()` runs `incus storage show default`
without sudo. If the user is not in the `incus-admin` group the command fails regardless
of whether storage is configured, causing `incus admin init --auto` to run and crash
with "storage has already been configured".

## Scope
- **In scope**: running the check with sudo privileges
- **Out of scope**: changes to storage backend selection or init behaviour

## Delta

### MODIFIED
- **Behaviour — Incus**: the already-initialised check runs with sudo so it succeeds
  for users not in the `incus-admin` group.
