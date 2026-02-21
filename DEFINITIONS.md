# Definitions


## Change Management Process
Project specifications are contained in `SPEC.md` files:
- The **root** `SPEC.md` covers the project as a whole (structure, shared requirements, integration testing).
- During spec changes, relevant assets such as proposals are stored in subfolders of the `changes` directory, which is placed alongside the relevant `SPEC.md`.
- Directory `SPEC.md` files are scoped to components in that directory and below — they own their own usage, implementation, and test definitions.
- Directory specs inherit project-wide non-functional requirements unless they explicitly override them.

A specification will typically follow a structure such as:
```markdown
# Specification
## Overview
## Usage
## Behaviour
## Constraints
## Verification
```

All changes to `SPEC.md` files must follow this four-phase process:

| Phase | Action | Output |
|-------|--------|--------|
| **1. Propose** | Define intent and scope of the change | `changes/<change-name>/proposal.md` |
| **2. Design** | Plan the technical approach and ordered task list | `changes/<change-name>/design.md` |
| **3. Implement** | Execute tasks one at a time, pausing for review after each | Updated code/tests |
| **4. Archive** | Apply the proposal delta to `SPEC.md`; move the change folder to `changes/archive/` | Updated `SPEC.md` |

Each phase requires explicit approval before the next begins.

> **Getting started**: When setting up a new project, create the initial `SPEC.md` directly. Once it is in place, use this process with the change name `initial-implementation` to design and carry out the first implementation.

> **Phase transitions**: Announce each move between phases clearly (e.g. "Proposal is ready for review", "Design is ready for review", "Implementation complete — ready to archive"). Do not proceed to the next phase without explicit approval.

### 1. Propose
Create a `proposal.md` in the `changes/<change-name>/` directory.

```markdown
# Proposal: <Change Name>
**Status: Note | Draft | Ready for Review | Approved**

## Unresolved (optional)
- Items not yet fully specified
- Use of this section indicates a proposal is not ready for review

## Intent
Why this change is needed.

## Scope
- **In scope**: what this change covers
- **Out of scope**: what is deferred

## Delta
Omit delta sections which aren't relevant.

### ADDED
- New requirements being introduced

### MODIFIED
- Existing requirements being changed (note previous values)

### REMOVED
- Requirements being eliminated
```

> **Notes**: A proposal with `Status: Note` is a deliberately minimal capture — a brief `Intent` and an `Unresolved` section are all that is required. Notes are parked intentionally and should not be treated as stalled drafts. They are picked up and elaborated into full proposals when the time is right; no other phases of the process apply until then.

The proposal must be reviewed and approved before proceeding.

### 2. Design
Create a `design.md` in the same change folder as the proposal. This captures the technical approach and an ordered task list. The design should explain *how* the approved spec changes will be realised in the codebase — this is where implementation-specific detail belongs (not in the proposal or spec).

```markdown
# Design: <Change Name>
**Status: Draft | Ready for Review | Approved**

## Approach
Technical explanation of how the change will be implemented,
referencing relevant code, libraries, and patterns.

## Tasks
- [ ] <implementation task>
- [ ] <implementation task>
- [ ] Run tests / verify
- [ ] Confirm implementation complete and ready to archive
```

Where the task list includes tests, they should be listed as separate tasks and, where possible, written before the code they verify (TDD style).

The design must be reviewed and approved before implementation begins.

### 3. Implement
Work through the task list one item at a time. Check off each task in `design.md` as it is completed. Pause after each task and invite the operator to review before proceeding to the next. Do not modify `SPEC.md` during this phase.

### 4. Archive
Apply the proposal delta to the `SPEC.md` alongside the `changes/` directory. Move the change folder to `changes/archive/YYYY-MM-DD-<change-name>/`.

