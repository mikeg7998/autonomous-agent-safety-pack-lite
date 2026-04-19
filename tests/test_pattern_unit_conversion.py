"""Aggregator: loads unit_conversion_tests/test_template.py under a
renamed module and re-exports every `test_*` symbol so pytest collects
them here."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_src = Path(__file__).resolve().parent.parent / "unit_conversion_tests" / "test_template.py"
_spec = importlib.util.spec_from_file_location("_uc_tests_loaded", _src)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_mod, _name)
