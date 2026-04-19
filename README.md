# Autonomous Agent Safety Pack — Lite (3 of 12 patterns, MIT)

Three defensive patterns for autonomous Python agents, open-sourced under MIT.
Each pattern is a single-folder drop-in: code, a `SKILL.md` explaining the
pattern and why it exists, an `install.sh`, and tests.

## Patterns

### `push_gate/`
A single chokepoint for every outbound side-effect in an agent system —
HTTP posts, webhook deliveries, message sends, email calls. Gives you rate
limits, payload deduplication, a circuit breaker, quiet hours, and an
append-only audit log, in one file, with no external dependencies beyond
the standard library.

### `unit_conversion_tests/`
A pytest regression template for unit assumptions at API boundaries. You
copy `test_template.py` into your project, point it at your real adapter,
and get test coverage over the four things that silently break when an
upstream changes unit: type, unit, scale, boundary.

### `git_filter_scrub/`
A hardened wrapper around `git-filter-repo` for removing secrets from
every commit in a repository's history, with a smoke test that proves it
actually did what it said it did on a planted secret.

## Install

Each pattern has its own `install.sh`. From the repo root:

```bash
./push_gate/install.sh
./unit_conversion_tests/install.sh
./git_filter_scrub/install.sh
```

Or use the top-level `install.sh` to install all three.

## Tests

```bash
python -m pytest tests/ -q
```

Each pattern's own tests also live alongside its source and can be run directly:

```bash
python -m pytest push_gate/test_push_gate.py -q
python -m pytest unit_conversion_tests/test_template.py -q
bash   git_filter_scrub/test_scrub.sh
```

## License

MIT. See `LICENSE`.

---

Full 12-pattern pack with additional modules available at safety-pack-landing.vercel.app
