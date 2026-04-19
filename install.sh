#!/usr/bin/env bash
# autonomous-agent-safety-pack-lite — top-level installer.
# Installs all 3 MIT patterns into a target agent directory.
#
# Usage:
#   SP_INSTALL_DIR=/path/to/your/agent ./install.sh
#
# Default SP_INSTALL_DIR is ./infrastructure.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SP_INSTALL_DIR="${SP_INSTALL_DIR:-infrastructure}"

for pattern in push_gate unit_conversion_tests git_filter_scrub; do
    echo ">>> installing $pattern -> $SP_INSTALL_DIR"
    bash "$HERE/$pattern/install.sh"
    echo ""
done

echo "All 3 patterns installed. Next:"
echo "  1. Read each pattern's SKILL.md."
echo "  2. Run: python -m pytest $HERE/tests/ -q"
