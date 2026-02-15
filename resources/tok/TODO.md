# TODO

- [ ] Replace clipboard tool detection with OSC 52
  - Remove `detect_clipboard()` — no longer needed
  - Rewrite `clipboard_copy()` to emit OSC 52: `\033]52;c;<base64-encoded data>\a`
  - Rewrite `clipboard_clear()` to emit OSC 52 with empty payload: `\033]52;c;!\a`
  - Write OSC 52 sequences to `/dev/tty` (not stdout) so they reach the terminal even when stdout is redirected
  - Remove the `clip` parameter threading through `main()` (no tool to detect/pass around)
- [ ] Update signal cleanup test
  - Current test uses a fake `xclip` binary — replace with capturing OSC 52 output (e.g. redirect `/dev/tty` or mock the write call)
