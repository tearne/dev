# Proposal: Add JSON LSP for Helix
**Status: Ready for Review**

## Intent
Helix currently has no language server configured for JSON files. Adding a JSON LSP
would provide schema validation, autocompletion, and hover documentation when editing
JSON files (e.g. `package.json`, config files).

## Scope
- **In scope**: installing a JSON LSP and adding its configuration to the Helix config
- **Out of scope**: YAML, TOML, or other data-format LSPs

## Delta

### ADDED
- `vscode-json-language-server` (from `vscode-langservers-extracted`, via `npm`) installed as part of the Helix toolchain
- Helix config includes language server entry for JSON files

### MODIFIED
- Tools Installed list gains `vscode-json-language-server`
- Helix config section notes the JSON LSP is configured
