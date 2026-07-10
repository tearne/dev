# Clarify Version-Check Distinction

## Intent

The installer has two different update-check mechanisms behind what looks like one TUI indicator: a release-version check (Helix, kitty) that always compares against the vendor's live latest release, and a pinned-SHA check (`grit` and other external tools) that compares against a pinned target in `external_scripts.toml` — which can itself lag the vendor's true latest until someone bumps the pin. Nothing today makes that distinction legible to someone reading the code or using the installer; a "Behind" or "[?]" indicator means something different depending on which mechanism produced it. Improve how that difference is surfaced.
