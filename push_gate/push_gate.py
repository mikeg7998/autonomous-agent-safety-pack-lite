"""
push_gate — centralized outbound gate with rate limits, dedup, circuit breaker.

Drop this in front of every external side-effect (HTTP POST, message send,
webhook, email). You control one chokepoint instead of auditing N call sites.

Usage:
    gate = PushGate(name="notifications", rate_per_min=20, dedup_window_s=60)

    def send(text):
        key = ("chat-123", text)
        with gate.reserve(key) as slot:
            if not slot.allowed:
                return slot.reason
            # perform the real outbound call here
            my_http_client.post(..., json={"text": text})
            slot.success()
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional


log = logging.getLogger("push_gate")


@dataclass
class Slot:
    allowed: bool
    reason: str = ""
    _on_success: Optional[Callable[[], None]] = None
    _on_failure: Optional[Callable[[], None]] = None

    def success(self) -> None:
        if self._on_success is not None:
            self._on_success()

    def failure(self) -> None:
        if self._on_failure is not None:
            self._on_failure()


@dataclass
class _RateBucket:
    capacity: int
    refill_per_sec: float
    tokens: float = 0.0
    last: float = field(default_factory=time.time)

    def take(self, now: float) -> bool:
        elapsed = max(0.0, now - self.last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.last = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


@dataclass
class _Breaker:
    threshold: int
    cooldown_s: float
    failures: int = 0
    opened_at: float = 0.0

    def is_open(self, now: float) -> bool:
        if self.failures < self.threshold:
            return False
        return (now - self.opened_at) < self.cooldown_s

    def record_failure(self, now: float) -> None:
        self.failures += 1
        if self.failures == self.threshold:
            self.opened_at = now

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = 0.0


class PushGate:
    """
    Rate-limited, deduplicated, circuit-broken outbound gate.

    - rate_per_min:     token bucket refill rate shared by ALL keys
    - dedup_window_s:   identical payloads suppressed within this window
    - breaker_threshold: consecutive failures before the gate short-circuits
    - breaker_cooldown_s: how long the breaker stays open after tripping
    - quiet_hours:      optional tuple (start_hour, end_hour) in local time;
                        messages dropped during this window unless allow_quiet=True
    - audit_path:       optional file where every decision is JSON-logged
    """

    def __init__(
        self,
        name: str,
        rate_per_min: int = 30,
        dedup_window_s: int = 60,
        breaker_threshold: int = 5,
        breaker_cooldown_s: int = 300,
        quiet_hours: Optional[tuple[int, int]] = None,
        audit_path: Optional[str] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.name = name
        self.dedup_window_s = dedup_window_s
        self.quiet_hours = quiet_hours
        self.audit_path = Path(audit_path) if audit_path else None
        self._clock = clock
        self._lock = threading.RLock()
        self._bucket = _RateBucket(capacity=rate_per_min, refill_per_sec=rate_per_min / 60.0, tokens=rate_per_min)
        self._breaker = _Breaker(threshold=breaker_threshold, cooldown_s=breaker_cooldown_s)
        self._seen: dict[str, float] = {}

    @contextmanager
    def reserve(self, key: Any, allow_quiet: bool = False):
        now = self._clock()
        fingerprint = self._fingerprint(key)

        with self._lock:
            self._evict_seen(now)

            if self._breaker.is_open(now):
                yield self._deny("breaker_open")
                return

            if self.quiet_hours and not allow_quiet and self._in_quiet_hours(now):
                yield self._deny("quiet_hours")
                return

            if fingerprint in self._seen:
                yield self._deny("duplicate")
                return

            if not self._bucket.take(now):
                yield self._deny("rate_limited")
                return

            self._seen[fingerprint] = now

        slot = Slot(
            allowed=True,
            _on_success=self._success_for(fingerprint),
            _on_failure=self._failure_for(fingerprint),
        )
        self._audit({"event": "allow", "fingerprint": fingerprint, "ts": now})
        try:
            yield slot
        except Exception:
            self._failure_for(fingerprint)()
            raise

    def _success_for(self, fingerprint: str) -> Callable[[], None]:
        def _inner() -> None:
            with self._lock:
                self._breaker.record_success()
            self._audit({"event": "success", "fingerprint": fingerprint, "ts": self._clock()})
        return _inner

    def _failure_for(self, fingerprint: str) -> Callable[[], None]:
        def _inner() -> None:
            now = self._clock()
            with self._lock:
                self._breaker.record_failure(now)
                self._seen.pop(fingerprint, None)
            self._audit({"event": "failure", "fingerprint": fingerprint, "ts": now})
        return _inner

    def _deny(self, reason: str) -> Slot:
        self._audit({"event": "deny", "reason": reason, "ts": self._clock()})
        return Slot(allowed=False, reason=reason)

    def _evict_seen(self, now: float) -> None:
        cutoff = now - self.dedup_window_s
        stale = [k for k, ts in self._seen.items() if ts < cutoff]
        for k in stale:
            del self._seen[k]

    def _in_quiet_hours(self, now: float) -> bool:
        hour = time.localtime(now).tm_hour
        start, end = self.quiet_hours  # type: ignore[misc]
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def _fingerprint(self, key: Any) -> str:
        if isinstance(key, str):
            raw = key
        else:
            raw = json.dumps(key, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _audit(self, entry: dict) -> None:
        entry["gate"] = self.name
        if self.audit_path is None:
            log.debug("push_gate: %s", entry)
            return
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError as exc:
            log.warning("push_gate audit write failed: %s", exc)


def gate_many(gate: PushGate, items: Iterable[Any]) -> list[tuple[Any, Slot]]:
    """Helper: reserve one slot per item, collect the results."""
    out: list[tuple[Any, Slot]] = []
    for item in items:
        with gate.reserve(item) as slot:
            out.append((item, slot))
    return out
