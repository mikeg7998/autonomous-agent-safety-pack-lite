"""Aggregator: runs git_filter_scrub/test_scrub.sh as a subprocess.

The shell test already handles its own `git-filter-repo not installed`
skip path by printing `SKIP:` and exiting 0, so any non-zero exit here
means a real failure."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def test_git_filter_scrub_smoke() -> None:
    script = Path(__file__).resolve().parent.parent / "git_filter_scrub" / "test_scrub.sh"
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash not on PATH")
    result = subprocess.run(
        [bash, str(script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if "SKIP: git-filter-repo not installed" in result.stdout:
        pytest.skip("git-filter-repo not installed on this host")
    assert result.returncode == 0, (
        f"test_scrub.sh failed (exit {result.returncode}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )
    assert "PASS" in result.stdout, f"expected PASS line; got:\n{result.stdout}"
