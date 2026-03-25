# Proposal: Lazy apt-get update
**Status: Draft**

## Intent
`apt-get update` currently runs unconditionally at the start of every install, even when no
apt-requiring items are selected. This is unnecessary (e.g. `--only rust`) and prevents
running the installer without sudo on hosts where only non-apt items are needed.

## Specification Deltas

### MODIFIED
- `apt-get update` runs at most once per invocation, and only when an apt installation is
  actually about to be performed. It does not run if no apt-requiring items are selected.
- The sudo password prompt runs at most once per invocation, and only when at least one
  selected item requires sudo. When sudo is needed, the prompt occurs before any
  installation work begins — never mid-run.
