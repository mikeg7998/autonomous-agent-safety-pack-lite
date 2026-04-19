"""
Tests for push_gate. Uses a fake clock so none of these tests sleep.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from push_gate import PushGate


class FakeClock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_gate(**kwargs) -> tuple[PushGate, FakeClock]:
    clock = FakeClock()
    gate = PushGate(
        name="test",
        rate_per_min=kwargs.pop("rate_per_min", 60),
        dedup_window_s=kwargs.pop("dedup_window_s", 60),
        breaker_threshold=kwargs.pop("breaker_threshold", 3),
        breaker_cooldown_s=kwargs.pop("breaker_cooldown_s", 120),
        clock=clock,
        **kwargs,
    )
    return gate, clock


def test_allow_once():
    gate, _ = make_gate()
    with gate.reserve("hello") as slot:
        assert slot.allowed
        slot.success()


def test_dedup_blocks_second_identical_call():
    gate, _ = make_gate()
    with gate.reserve("hello") as slot:
        assert slot.allowed
        slot.success()
    with gate.reserve("hello") as slot:
        assert not slot.allowed
        assert slot.reason == "duplicate"


def test_dedup_expires_after_window():
    gate, clock = make_gate(dedup_window_s=60)
    with gate.reserve("x") as slot:
        assert slot.allowed
        slot.success()
    clock.advance(61)
    with gate.reserve("x") as slot:
        assert slot.allowed


def test_rate_limit_trips_after_capacity():
    gate, _ = make_gate(rate_per_min=3, dedup_window_s=0)
    for i in range(3):
        with gate.reserve(f"m{i}") as slot:
            assert slot.allowed, f"message {i} should have passed"
            slot.success()
    with gate.reserve("m3") as slot:
        assert not slot.allowed
        assert slot.reason == "rate_limited"


def test_rate_refills_over_time():
    gate, clock = make_gate(rate_per_min=60, dedup_window_s=0)
    for i in range(60):
        with gate.reserve(f"m{i}") as slot:
            assert slot.allowed
            slot.success()
    with gate.reserve("over") as slot:
        assert not slot.allowed
    clock.advance(2)
    with gate.reserve("after-wait") as slot:
        assert slot.allowed


def test_breaker_opens_after_failures():
    gate, _ = make_gate(breaker_threshold=2, dedup_window_s=0)
    for key in ("a", "b"):
        with gate.reserve(key) as slot:
            assert slot.allowed
            slot.failure()
    with gate.reserve("c") as slot:
        assert not slot.allowed
        assert slot.reason == "breaker_open"


def test_breaker_closes_after_cooldown():
    gate, clock = make_gate(breaker_threshold=2, breaker_cooldown_s=30, dedup_window_s=0)
    for key in ("a", "b"):
        with gate.reserve(key) as slot:
            slot.failure()
    clock.advance(31)
    with gate.reserve("c") as slot:
        assert slot.allowed
        slot.success()


def test_success_resets_breaker_counter():
    gate, _ = make_gate(breaker_threshold=3, dedup_window_s=0)
    with gate.reserve("a") as slot:
        slot.failure()
    with gate.reserve("b") as slot:
        slot.success()
    with gate.reserve("c") as slot:
        slot.failure()
    with gate.reserve("d") as slot:
        assert slot.allowed


def test_quiet_hours_block_messages():
    class ScheduledClock(FakeClock):
        pass

    clock = ScheduledClock()
    import time as _time
    fixed_struct = _time.struct_time((2026, 4, 18, 2, 30, 0, 5, 108, 0))
    original = _time.localtime
    _time.localtime = lambda *_a, **_k: fixed_struct
    try:
        gate = PushGate(
            name="test",
            rate_per_min=60,
            dedup_window_s=0,
            quiet_hours=(22, 7),
            clock=clock,
        )
        with gate.reserve("night") as slot:
            assert not slot.allowed
            assert slot.reason == "quiet_hours"
        with gate.reserve("urgent", allow_quiet=True) as slot:
            assert slot.allowed
    finally:
        _time.localtime = original


def test_audit_log_written(tmp_path: Path):
    audit = tmp_path / "audit.jsonl"
    gate = PushGate(
        name="test",
        rate_per_min=60,
        dedup_window_s=0,
        audit_path=str(audit),
    )
    with gate.reserve("hello") as slot:
        slot.success()
    lines = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    events = [entry["event"] for entry in lines]
    assert "allow" in events
    assert "success" in events


def test_failure_clears_dedup_so_caller_can_retry():
    gate, _ = make_gate(dedup_window_s=60, breaker_threshold=99)
    with gate.reserve("retryable") as slot:
        assert slot.allowed
        slot.failure()
    with gate.reserve("retryable") as slot:
        assert slot.allowed


def test_exception_in_block_counts_as_failure():
    gate, _ = make_gate(breaker_threshold=2, dedup_window_s=0)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            with gate.reserve("boom") as slot:
                assert slot.allowed
                raise RuntimeError("downstream blew up")
    with gate.reserve("next") as slot:
        assert not slot.allowed
        assert slot.reason == "breaker_open"
