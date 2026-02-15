#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="test-setup"
IMAGE="images:ubuntu/24.04"

if ! command -v incus &>/dev/null; then
    echo "Error: incus not found. Install incus first."
    exit 1
fi

# Clean up any existing container
if incus info "$CONTAINER" &>/dev/null; then
    echo "Deleting existing container '$CONTAINER'..."
    incus delete "$CONTAINER" --force
fi

echo "Launching $IMAGE as '$CONTAINER'..."
incus launch "$IMAGE" "$CONTAINER"

echo "Waiting for networking..."
sleep 5

echo "Pushing setup files into container..."
incus exec "$CONTAINER" -- mkdir -p /root/setup
incus file push "$SCRIPT_DIR/bootstrap_inst.sh" "$CONTAINER/root/setup/"
incus file push "$SCRIPT_DIR/install.py" "$CONTAINER/root/setup/"
incus file push -r "$SCRIPT_DIR/resources" "$CONTAINER/root/setup/"

echo "Running setup inside container..."
echo "============================================================"
incus exec "$CONTAINER" -- bash /root/setup/bootstrap_inst.sh
echo "============================================================"

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

FAILURES=0
fail() { echo "  FAIL: $1"; FAILURES=$((FAILURES + 1)); }
pass() { echo "  PASS: $1"; }
cexec() { incus exec "$CONTAINER" -- bash -c "$1"; }

echo ""
echo "=== Post-setup verification ==="

# --- Tool installation (10 checks) ---
for tool in htop btop incus rustc cargo zellij hx harper-ls pyright ruff; do
    if cexec "export PATH=\"\$HOME/.cargo/bin:\$HOME/.local/bin:\$PATH\" && command -v $tool" &>/dev/null; then
        pass "$tool installed"
    else
        fail "$tool installed"
    fi
done

# --- Symlinks (3 checks) ---
check_symlink() {
    local path="$1" expected="$2" label="$3"
    actual=$(cexec "readlink $path" 2>/dev/null) || actual=""
    if [ "$actual" = "$expected" ]; then
        pass "$label"
    else
        fail "$label (expected '$expected', got '$actual')"
    fi
}

check_symlink ~/.config/helix/config.toml   "../../setup/resources/helix/config.toml"   "config.toml symlink"
check_symlink ~/.config/helix/languages.toml "../../setup/resources/helix/languages.toml" "languages.toml symlink"
check_symlink ~/.local/bin/tok               "../../setup/resources/tok/tok.py"            "tok symlink"

# --- PATH (1 check) ---
if cexec "bash --login -c 'echo \$PATH'" 2>/dev/null | grep -q '\.local/bin'; then
    pass ".local/bin on PATH"
else
    fail ".local/bin on PATH"
fi

# --- Config content (2 checks) ---
if cexec "grep -q 'theme = \"autumn\"' ~/.config/helix/config.toml"; then
    pass "config.toml contains theme = autumn"
else
    fail "config.toml contains theme = autumn"
fi

if cexec "grep -q 'dialect = \"British\"' ~/.config/helix/languages.toml"; then
    pass "languages.toml contains dialect = British"
else
    fail "languages.toml contains dialect = British"
fi

# --- Config-not-overwritten (2 checks) ---
echo ""
echo "=== Config-not-overwritten test ==="

# Replace the config.toml symlink with a decoy regular file
cexec "rm -f ~/.config/helix/config.toml"
cexec "echo 'theme = \"catppuccin\"' > ~/.config/helix/config.toml"

# Re-run setup and capture output
SETUP_OUTPUT=$(incus exec "$CONTAINER" -- bash /root/setup/bootstrap_inst.sh 2>&1) || true

if cexec "grep -q 'theme = \"catppuccin\"' ~/.config/helix/config.toml"; then
    pass "existing config not overwritten"
else
    fail "existing config not overwritten"
fi

if echo "$SETUP_OUTPUT" | grep -q "WARNING.*not overwriting"; then
    pass "warning emitted for existing config"
else
    fail "warning emitted for existing config"
fi

# --- Install log (2 checks) ---
echo ""
echo "=== Install log test ==="

if cexec "test -f /root/setup/install.log"; then
    pass "install.log exists"
else
    fail "install.log exists"
fi

if cexec "grep -qP '\\e\\[' /root/setup/install.log"; then
    fail "install.log contains no ANSI escapes"
else
    pass "install.log contains no ANSI escapes"
fi

# --- Summary ---
echo ""
TOTAL=$((18 + 2))
if [ "$FAILURES" -eq 0 ]; then
    echo "All $TOTAL checks passed."
else
    echo "$FAILURES of $TOTAL checks failed."
fi

echo ""
echo "Container '$CONTAINER' is still running."
echo "  Shell in:  incus exec $CONTAINER -- bash"
echo "  Delete:    incus delete $CONTAINER --force"

if [ "$FAILURES" -gt 0 ]; then exit 1; fi
