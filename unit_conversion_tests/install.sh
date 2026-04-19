#!/usr/bin/env bash
# unit_conversion_tests — drop-in installer.
# Copies the template test and example adapter into your project.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${SP_INSTALL_DIR:-tests/unit_contracts}"
EXAMPLE_DEST="${SP_EXAMPLE_DIR:-adapters}"

mkdir -p "$DEST" "$EXAMPLE_DEST"
cp "$HERE/test_template.py" "$DEST/test_template.py"
cp "$HERE/example_api_wrapper.py" "$EXAMPLE_DEST/example_api_wrapper.py"

echo "Installed:"
echo "  $DEST/test_template.py"
echo "  $EXAMPLE_DEST/example_api_wrapper.py"
echo ""
echo "Next:"
echo "  1. Rename test_template.py to match the adapter it is testing."
echo "  2. Change the import to point at YOUR adapter."
echo "  3. Replace simulated_api_response() with your real upstream shape."
echo "  4. Run: pytest $DEST/"
