"""
Each pattern keeps its authoritative test file next to its source
(e.g. push_gate/test_push_gate.py). `tests/` contains thin aggregator
files that load those tests under renamed modules so `pytest tests/`
collects them without colliding with the pattern-local layout.

This conftest puts each pattern directory on sys.path so the aggregators
can import the patterns.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _pattern in ("push_gate", "unit_conversion_tests", "git_filter_scrub"):
    _p = str(_ROOT / _pattern)
    if _p not in sys.path:
        sys.path.insert(0, _p)
