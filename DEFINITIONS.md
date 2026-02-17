# Definitions

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
- Rather than complex configuration, set the script up with key functions at the top of the file, so they can be easily commented out or used to jump to navigate.
- Keep utility functions towards the bottom of the file.
- Guard against being run directly (e.g. `python3 script.py`) instead of via `uv run`. Check for `VIRTUAL_ENV` or `UV_INTERNAL__PARENT_INTERPRETER` in the environment and exit with a helpful message if neither is set. Use the pattern:
    ```py
    if not (os.environ.get("VIRTUAL_ENV") or os.environ.get("UV_INTERNAL__PARENT_INTERPRETER")):
        print("Error: run this script via './<script>' or bootstrap_inst.sh, not directly.")
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
