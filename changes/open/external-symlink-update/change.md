# External Symlink Update
**Type**: Fix
**Status**: Approved

## Log

When upgrading an external script to a new SHA, `install_external_script` warns "already exists, not overwriting" instead of replacing the symlink. The guard was intended to protect manually-placed binaries, but a symlink pointing to any version of the installer's own cache should always be replaced. Only a non-symlink file at the destination warrants a warning.
