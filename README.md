# Autonomous Agent Safety Pack — Lite

Three drop-in patterns for anyone running autonomous agents that touch
money, messages, or paid APIs.

These are 3 of the 12 patterns from the full
[OpenClaw Update Fix Pack](https://safety-pack-landing.vercel.app).

## What's here

| Pattern | What it prevents |
|---|---|
| `push_gate` | Runaway Telegram/Slack rate-limit bans, dedup spam, circuit-breaker meltdowns |
| `unit_conversion_tests` | Silent 100x bugs from unit/type/scale mismatches |
| `git_filter_scrub` | Accidentally committed secrets in git history |

## Install

Drop the pattern folder into your project. No framework, no
dependencies beyond the standard library. Python 3.11+ for the two
Python patterns; `git_filter_scrub` is a bash wrapper around
[`git-filter-repo`](https://github.com/newren/git-filter-repo).

## Test

```bash
cd push_gate && python -m pytest tests/
cd unit_conversion_tests && python -m pytest tests/
cd git_filter_scrub && bash tests/test_scrub.sh
```

(`git_filter_scrub` tests will SKIP cleanly if `git-filter-repo` is
not installed.)

## The full pack

The other 9 patterns cover: human-in-loop money approval, API credit
caps, allowlist filtering, LLM provider fallback, proximity-based
rate tiering, OpenClaw update survival (snapshot/canary/rollback),
plugin manifest pinning, config schema drift detection, and agent
health watchdog.

→ [safety-pack-landing.vercel.app](https://safety-pack-landing.vercel.app)

## License

MIT — use these however you want, no attribution required.
