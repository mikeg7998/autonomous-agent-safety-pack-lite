#!/usr/bin/env bash
# git_filter_scrub — drop-in installer.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${SP_INSTALL_DIR:-tools/git_filter_scrub}"

mkdir -p "$DEST"
cp "$HERE/scrub.sh" "$DEST/scrub.sh"
chmod +x "$DEST/scrub.sh"

echo "Installed scrub.sh -> $DEST/scrub.sh"
echo ""
echo "Prereqs: git and git-filter-repo (pip install git-filter-repo)"
echo ""
echo "Next:"
echo "  1. Write tokens.txt with '<secret>==><REDACTED>' per line."
echo "  2. bash $DEST/scrub.sh /path/to/repo tokens.txt /tmp/scrub-out"
echo "  3. Force-push and rotate the leaked secrets."
