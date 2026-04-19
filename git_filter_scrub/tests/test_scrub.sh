#!/usr/bin/env bash
# Smoke test for scrub.sh. Creates a local repo with a planted secret,
# runs the scrubber, verifies the secret is gone from history.
# Requires: git, git-filter-repo, bash.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRUB="$HERE/scrub.sh"

command -v git-filter-repo >/dev/null 2>&1 || {
    echo "SKIP: git-filter-repo not installed"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> build sample repo"
mkdir -p "$TMP/src"
pushd "$TMP/src" >/dev/null
git init -q
git config user.email "test@example.com"
git config user.name "Test"
echo "SECRET_TOKEN=fake_12345_shouldnotbehere" >.env
git add .env
git commit -q -m "accidentally commit secret"
echo "public content" >README.md
git add README.md
git commit -q -m "add readme"
popd >/dev/null

echo "==> write tokens file"
cat >"$TMP/tokens.txt" <<EOF
fake_12345_shouldnotbehere==><REDACTED>
EOF

echo "==> run scrub"
bash "$SCRUB" "$TMP/src" "$TMP/tokens.txt" "$TMP/out"

echo "==> verify secret not present in rewritten mirror"
HISTORY="$(git -C "$TMP/out/mirror.git" log --all -p 2>/dev/null)"
if printf '%s' "$HISTORY" | grep -F -q "fake_12345_shouldnotbehere"; then
    echo "FAIL: secret still in history"
    exit 1
fi

echo "==> verify placeholder IS present"
if ! printf '%s' "$HISTORY" | grep -F -q "<REDACTED>"; then
    echo "FAIL: placeholder not written"
    exit 1
fi

echo "PASS"
