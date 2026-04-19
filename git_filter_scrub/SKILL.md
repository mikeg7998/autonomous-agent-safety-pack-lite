# git_filter_scrub

**What:** A hardened wrapper around `git-filter-repo` for removing
secrets from every commit in a repository's history, with a smoke test
that proves it actually did what it said it did on a planted secret.

**Why:** Everybody commits a key at some point. `git rm` on the current
commit does not help — the secret is still in every prior commit, every
branch, every tag, and every clone. The correct fix is to rewrite
history and then rotate the secret, in that order, with full awareness
that the rewrite is destructive to collaborators' existing clones.

`git filter-branch` is slow and error-prone. `bfg` is faster but
drops support for several edge cases. `git-filter-repo` is the
current recommendation from the Git project itself. This skill wraps
it in a flow you can run without memorizing flags.

**Pattern (what the wrapper enforces):**

1. **Mirror-clone first.** Never scrub in place. A mirror clone is a
   safe copy the rewrite can mutate; if it goes wrong, you delete the
   mirror and start over.
2. **Tokens in a file, not the CLI.** `<secret>==><REDACTED>` one per
   line. Shell quoting bugs around literal secret values on a command
   line are exactly the place you do not want a typo.
3. **Verify on the rewritten mirror.** The script re-greps the tokens
   file against the mirror and fails loudly if any token is still
   findable.
4. **Loud next-step reminders.** The output tells you to force-push
   AND to rotate the secret AND to ask collaborators to re-clone.
   History rewriting does NOT revoke a leaked credential — someone
   else may have cloned the original history before the rewrite.

**Usage:**

```bash
cat >tokens.txt <<EOF
YOUR_LEAKED_API_KEY_VALUE==><REDACTED>
MY_ACCESS_TOKEN_VALUE==><REDACTED>
EOF

bash scrub.sh /path/to/repo tokens.txt /tmp/scrub-out
```

Then:

```bash
cd /tmp/scrub-out/mirror.git
git push --force --all
git push --force --tags
```

Then rotate every token at the provider and ask every collaborator to
re-clone.

**What this is NOT:**

- Not a substitute for secret rotation. Rotate every leaked secret.
  Assume the worst — that someone cloned the repo before you ran
  this.
- Not a replacement for secret scanning on commit. Add a pre-commit
  hook (e.g. gitleaks) so this tool is needed once per career, not
  monthly.
- Not safe for a shared branch without coordination. Force-push
  blasts collaborators' local state. Tell them first.

**Smoke test:** `bash test_scrub.sh` builds a throwaway repo with a
planted fake secret, runs the scrubber against it, asserts the
secret is absent and the placeholder is present.

**Tested on:** git 2.34+, git-filter-repo 2.38+. The test SKIPs if
`git-filter-repo` is not on `PATH`.

**Install:** `bash install.sh`.
