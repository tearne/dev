# Proposal: Review Node.js LSP Installation Strategy
**Status: Note**

## Unresolved
- With `vscode-json-language-server` added via `npm`, there are now two Node.js-based
  LSPs: `pyright` (installed via `uv`) and `vscode-json-language-server` (installed via
  `npm`). Should Node.js LSPs be installed consistently through a single mechanism?
  Should `npm` be a first-class install method, and if so, does `pyright` move to it?

## Intent
The project now installs Node.js-based language servers via two different mechanisms
(`uv` for `pyright`, `npm` for `vscode-json-language-server`). This note parks the
question of whether to consolidate on a single install strategy for Node.js tooling,
and whether that has implications for future LSPs.
