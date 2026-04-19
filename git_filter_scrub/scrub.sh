#!/usr/bin/env bash
# scrub.sh — nuke secrets from a git repository's full history.
#
# Wraps git-filter-repo with a predictable, audit-friendly flow:
#   1. Hard mirror-clone into a sibling directory.
#   2. Build a replace-expressions file from a token file you pass in.
#   3. Run git-filter-repo with --replace-text over the mirror.
#   4. Print verification grep (must return ZERO matches).
#   5. Remind the user to force-push to all remotes and rotate the
#      secrets — history rewriting does NOT invalidate the old secret.
#
# Usage:
#   ./scrub.sh path/to/repo.git tokens.txt /tmp/scrub_output
#
# tokens.txt format, one per line:
#   <secret-value>==><REDACTED>
#   <your-leaked-token>==><REDACTED>
#   "MY_API_KEY"==>"MY_API_KEY_REDACTED"
#
# Requires: git, git-filter-repo.

set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 3 ]]; then
    cat <<EOF
Usage: $0 <source-repo> <tokens-file> <work-dir>

  <source-repo>   path or URL of a repo to rewrite
  <tokens-file>   replace-expressions file (see header)
  <work-dir>      directory to clone into (created if missing)

After success:
  - git push --force --all  (and --tags) from <work-dir>
  - rotate every leaked secret at the provider; history rewrite does
    not invalidate what leaked.
EOF
    exit 1
fi

SRC="$1"
TOKENS="$2"
WORK="$3"

command -v git >/dev/null 2>&1 || { echo "ERROR: git not installed"; exit 1; }
command -v git-filter-repo >/dev/null 2>&1 || {
    echo "ERROR: git-filter-repo not installed"
    echo "  pip install git-filter-repo"
    exit 1
}

[[ -r "$TOKENS" ]] || { echo "ERROR: tokens file not readable: $TOKENS"; exit 1; }

echo "==> clone mirror"
mkdir -p "$WORK"
CLONE="$WORK/mirror.git"
[[ -e "$CLONE" ]] && { echo "ERROR: $CLONE already exists. Move or delete it."; exit 1; }
git clone --mirror "$SRC" "$CLONE"

echo "==> rewrite history"
pushd "$CLONE" >/dev/null
git-filter-repo --replace-text "../$(basename "$TOKENS")" --force || {
    # git-filter-repo expects tokens file to be reachable; copy it in.
    cp "$TOKENS" "$CLONE/tokens.txt"
    git-filter-repo --replace-text "$CLONE/tokens.txt" --force
}
popd >/dev/null

echo "==> verify (must return nothing)"
HISTORY_DUMP="$(git -C "$CLONE" log --all -p 2>/dev/null)"
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    token="${line%%==>*}"
    [[ -z "$token" ]] && continue
    if printf '%s' "$HISTORY_DUMP" | grep -F -q "$token"; then
        echo "  FOUND '$token' still present — rewrite did not cover it"
        exit 2
    fi
done <"$TOKENS"

echo "==> OK"
cat <<'NEXT'

NEXT STEPS:
  1. cd into the rewritten mirror and force-push:
       cd "$WORK/mirror.git"
       git push --force --all
       git push --force --tags

  2. Rotate every secret at the provider. History rewriting does not
     revoke a leaked credential — an attacker may already have cloned
     the pre-rewrite history.

  3. Ask every collaborator to re-clone. Their existing clones still
     contain the unrewritten history.
NEXT
