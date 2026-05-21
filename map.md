# devenv

[Down](#install-layers)

A dev environment installer with two install layers — apt for system foundations, `~/.local/` for the user-space application stack — kept independently updatable so a refresh of one does not disturb the other. This project owns the user-space layer's updates; apt manages its own. Testing mirrors that isolation: runs without containers, never mutates the host.

```
devenv
├ Install Layers
│ ├ System (apt)
│ └ User-space (TODO)
├ Update Strategy (TODO)
└ Testing Discipline (TODO)
  ├ Container-free (TODO)
  └ No system mutation (TODO)
```


# Install Layers

[Up](#devenv)
[Down](#system-apt)
[Down](#user-space)

Two layers with separate update cadences. The lower layer is system foundations and trivial tools installed via apt; `unattended-upgrades` applies security and OS fixes automatically. The upper layer — editors, language servers, hand-picked binaries — lives under `~/.local/` and refreshes manually when the user re-runs this project.

> [!IMPORTANT] The split protects each cadence from the other. Automatic apt updates never touch user-space tools, so the user never has to delay or disable `unattended-upgrades` to keep their working stack stable; equally, a manual user-space refresh never disturbs the system layer.


# System (apt)

[Up](#install-layers)

The apt-managed layer. Holds system foundations and lightweight utilities — content where the user is happy for apt to handle updates automatically. Installation and updates both go through apt; `unattended-upgrades` runs the upgrade pass daily without user intervention.

**Detail**

Inventory:

- `build-essential`
- `git`
- `htop`
- `btop`
- `tree`
- `wl-clipboard`
- `xclip`
- `incus`
- `unattended-upgrades`
- `libatomic1` (transparent pyright runtime dep)

Cadence comes from the apt package: `APT::Periodic::Unattended-Upgrade "1"` (daily) in `/etc/apt/apt.conf.d/20auto-upgrades`, executed by systemd's `apt-daily-upgrade.timer` (≤60 min random delay, catches up after missed runs). This project's only configuration is `/etc/apt/apt.conf.d/99unattended-upgrades-all-origins`, extending `Allowed-Origins` from security-only to `*:*`.
