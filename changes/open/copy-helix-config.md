# Copy Helix Config Instead of Symlinking

## Intent

Helix config files (`config.toml`, `languages.toml`) are currently symlinked from `~/.config/helix/` into the repo's `resources/helix/` directory. This makes them vulnerable to accidental deletion — removing the target-side file actually destroys the repo copy. Switching to a file copy would make the deployed config independent of the repo, eliminating that risk. The config update path also needs rethinking: the current `_link_helix_config()` skips work when the binary is already installed and the symlink is correct, but a copy-based approach would need a way to detect when the source template has changed and offer to update the deployed copy.
