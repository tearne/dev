# Rudimentary Map

## Intent

Capture the six principles the user most cares about as the seed of `map.md` — a rudimentary first cut with enough structure for navigation, not yet a complete map.

## Approach

The map uses the standard tree-of-nodes format (per `MAP-GUIDANCE.md`). Drafting follows the per-node negotiation pattern: one node at a time, comprehension checks, no bulk pre-staging.

### Top-level shape (agreed)

```
devenv
├ Install Layers
│ ├ System (apt)
│ └ User-space
├ Update Strategy
└ Testing Discipline
  ├ Container-free
  └ No system mutation
```

Six source principles map to nodes as follows: 1+4+5 → Install Layers; 1+6 → Update Strategy; 2+3 → Testing Discipline. (The principles themselves are recorded in chat history at session opening.)

### Decisions logged so far

- **Install Layers carries an `[!IMPORTANT]` callout.** The split is about *cadence*, not storage location. Each cadence protected from the other: automatic apt updates never touch user-space tools, and manual user-space refresh never disturbs the system layer.
- **System (apt) `**Detail**` consolidates inventory and cadence.** Ten packages listed (including `libatomic1` annotated as a transparent pyright runtime dep). Cadence: apt package defaults (`APT::Periodic::Unattended-Upgrade "1"`, `apt-daily-upgrade.timer`); this project owns only the all-origins override at `/etc/apt/apt.conf.d/99unattended-upgrades-all-origins`.
- **User-space heading drops its original parenthetical `(~/.local, tarballs)`.** Heading anchors don't survive `~`, `/`, `.`, `,` cleanly; descriptive content moves into the node body when drafted.

### Out of scope

No version bump (map drafting is documentation, not installer behaviour). No `active.md` — map work is exempt from the active-change requirement per `MAP-GUIDANCE.md`.

## Plan

Nodes drafted:

- [x] `devenv` (root)
- [x] `Install Layers`
- [x] `System (apt)`

Nodes pending:

- [ ] `User-space`
- [ ] `Update Strategy`
- [ ] `Testing Discipline`
- [ ] `Container-free`
- [ ] `No system mutation`
- [ ] Review the map as a whole once all nodes are drafted; adjust the root prose if needed.

## Log

- Open thread: a `process:` entry in `changes/process-feedback.md` (2026-05-01) proposes scoping the "blank line between bullet points" rule to sentence-shaped wrappable bullets only. Once settled in `MAP-GUIDANCE.md`, a sweep across `map.md` may be needed.
