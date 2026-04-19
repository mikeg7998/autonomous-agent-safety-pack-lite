#!/usr/bin/env bash
# push_gate — drop-in installer.
# Copies push_gate.py into your project. No dependencies to install.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${SP_INSTALL_DIR:-infrastructure}"

mkdir -p "$DEST"
cp "$HERE/push_gate.py" "$DEST/push_gate.py"

echo "Installed push_gate.py -> $DEST/push_gate.py"
echo ""
echo "Next:"
echo "  1. Wrap every outbound call site with gate.reserve(...)."
echo "  2. Set audit_path to a file your log pipeline already watches."
echo "  3. Run: pytest $HERE/test_push_gate.py"
