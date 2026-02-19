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

All changes to `SPEC.md` files must follow this process:

> **Phase transitions**: Announce each move between phases clearly (e.g. "Proposal is ready for review", "Design is ready for review", "Implementation complete — ready to archive"). Do not proceed to the next phase without explicit approval.

### 1. Propose
Create a `proposal.md` in the `changes/<change-name>/` directory.

```markdown
# Proposal: <Change Name>
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

The proposal must be reviewed and approved before proceeding.

### 2. Design
Create a `design.md` in the same change folder as the proposal. This captures the technical approach and an ordered task list. The design should explain *how* the approved spec changes will be realised in the codebase — this is where implementation-specific detail belongs (not in the proposal or spec).

```markdown
# Design: <Change Name>

## Approach
Technical explanation of how the change will be implemented,
referencing relevant code, libraries, and patterns.

## Tasks
1. <implementation task>
2. <implementation task>
3. Run tests / verify
```

Where the task list includes tests, they should be listed as separate tasks and, where possible, written before the code they verify (TDD style).

The design must be reviewed and approved before implementation begins.

### 3. Implement
Work through the task list one item at a time. Pause after each task and invite the operator to review before proceeding to the next. Do not modify `SPEC.md` during this phase.

### 4. Archive
Apply the proposal delta to the `SPEC.md` alongside the `changes/` directory. Move the change folder to `changes/archive/YYYY-MM-DD-<change-name>/`.



## Python Orchestrated Script (POS)
The POS style helps Python take the place of native shell scripts. It strategically breaks some Python idioms to combine the different strengths of Python and shell scripts, such as favouring subprocess calls for shell commands while using Python control flow.

POS guidance:
- If there is a reasonably simple command to achieve a task in the shell, prefer running that command in a subprocess over the equivalent Pythonic code. Use Python for control flow.
- This makes it easier for users to discover commands they may want to copy and paste into a terminal.
    - Examples:
        - To download the latest version of the `helix` `deb` for `amd64`:
        ```py
        subprocess.run(r"""curl -s https://api.github.com/repos/helix-editor/helix/releases/latest | grep -oP '"browser_download_url": "\K[^"]*amd64.deb' | xargs wget""")
        ```
        - To apt install `curl`:
        ```py
        subprocess.run("""DEBIAN_FRONTEND=noninteractive apt-get install -y curl""")
        ```
    - But don't take this to an extreme and force trivial actions like loops into the shell.
- Prefer a single Python source file, unless it compromises readability.
- Make the python file executable and use a `uv` shebang.
```sh
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.12.*"
# ///
```
- Rather than complex configuration, set the script up with key functions at the top of the file, so they can be easily commented out or jumped to.
- Keep utility functions towards the bottom of the file.
- Guard against being run directly (e.g. `python3 script.py`) instead of via `uv run`. Check for `VIRTUAL_ENV` or `UV_INTERNAL__PARENT_INTERPRETER` in the environment and exit with a helpful message if neither is set. Use the pattern:
    ```py
    if not (os.environ.get("VIRTUAL_ENV") or os.environ.get("UV_INTERNAL__PARENT_INTERPRETER")):
        print("Error: run this script via './<script-name>', not directly.")
        sys.exit(1)
    ```
- Try to keep to built-in Python libraries to maximise future compatibility. Suggested libraries (when relevant):
    - Built-in:
        - `argparse` — CLI argument parsing
        - `getpass` — prompting for passwords without echo
        - `os` — environment variables, process management
        - `pathlib` — filesystem path manipulation
        - `shutil` — file/directory copy and removal
        - `subprocess` — running shell commands
        - `sys` — exit codes, interpreter info
        - `time` — delays and simple timing
    - External (pre-approved):
        - `rich` — formatted terminal output, progress bars, tables

