# Switch Markdown Language Server to Marksman

## Intent

In-document heading links (`[Up](#heading)`) in map files don't navigate to their targets — the current markdown language server doesn't support go-to-definition for fragment-only anchors. The replacement that was avoided previously due to a heavy runtime dependency now ships as a standalone binary, removing that concern.

## Approach

Replace markdown-oxide with marksman across three files:

- **`resources/helix/languages.toml`** — swap the `[language-server.markdown-oxide]` block for a `[language-server.marksman]` block and update the markdown `language-servers` list.
- **`install.py`** — replace `install_markdown_oxide()` with `install_marksman()`. Marksman publishes GitHub release binaries per architecture, so follow the same pattern as biome: download the arch-appropriate binary to `~/.local/bin/marksman` and `chmod +x`. Update the `InstallItem` entry (name, function, remove `requires=["cargo-binstall"]`, change `install_check`).
- **`SPEC.md`** — update the tool tree, item interdependencies, installation method table, installation order notes, and integration test expectations to reference marksman instead of markdown-oxide.

No version pinning — latest stable release, consistent with all other tools. No moxide-specific config files exist to clean up.

## Plan

- [x] UPDATE `resources/helix/languages.toml` — replace the `markdown-oxide` language server block with `marksman` (command: `marksman`, no args needed) and update the markdown `language-servers` list
- [x] UPDATE `install.py` — replace `install_markdown_oxide()` with `install_marksman()` using the GitHub releases pattern (match biome's approach for arch detection and binary download); update the `InstallItem` registration to remove the `cargo-binstall` dependency
- [x] UPDATE `tests/integration.py` — remove `"markdown-oxide"` from `SKIP_WITHOUT_GCC` (marksman is a pre-built binary, not a cargo-binstall dependent)
- [x] UPDATE `SPEC.md` — replace all markdown-oxide references with marksman: tool tree, item interdependencies, installation method (move from `cargo binstall` to GitHub releases), installation order (remove from stage 4 cargo-binstall dependents), and integration test callable list
- [x] REVIEW full change for consistency across all four files

## Conclusion

Completed as planned. Marksman installed and confirmed working.
