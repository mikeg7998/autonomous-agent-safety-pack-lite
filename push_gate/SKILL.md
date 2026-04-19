# push_gate

**What:** A single chokepoint for every outbound side-effect in an agent
system — HTTP posts, webhook deliveries, message sends, email calls. Gives
you rate limits, payload deduplication, a circuit breaker, quiet hours, and
an append-only audit log, in one file, with no external dependencies beyond
the standard library.

**Why:** Without a gate, every new bot adds another place where bad state
can escape to the outside world. I spent two weekends chasing a feedback
loop where two agents alerted each other into a 400-message burst at 3 AM.
A single `PushGate` would have caught it on message four. The fix is
architectural, not a retry-after knob on one script.

**Pattern (four properties every outbound gate should have):**

1. **Rate limit.** Token bucket, shared across all callers. Caps bursts
   regardless of which code path fires them.
2. **Deduplication.** A content fingerprint in a time window. Stops the
   "same alert fired by three bots" case that rate limits alone miss when
   the bucket is fresh.
3. **Circuit breaker.** After N consecutive failures, the gate refuses all
   traffic for a cooldown. Stops the "downstream is dead, let's retry 500
   times" pattern.
4. **Audit log.** Every allow/deny/success/failure on one JSONL file. You
   can reconstruct what the system was doing during an incident without
   attaching a debugger.

Optional:

5. **Quiet hours.** A tuple of `(start_hour, end_hour)` in local time.
   Useful when the system does not need to alert a human at 3 AM.
6. **Override flag.** `allow_quiet=True` skips the quiet-hours check for a
   genuine page.

**Where it does NOT belong:**

- Inside a hot inner loop where latency matters more than safety.
- In front of idempotent reads. This is for side effects.
- As your only line of defense. Still validate inputs at the system edge.

**Usage:**

```python
from push_gate import PushGate

gate = PushGate(
    name="notifications",
    rate_per_min=20,
    dedup_window_s=60,
    breaker_threshold=5,
    breaker_cooldown_s=300,
    quiet_hours=(22, 7),
    audit_path="/var/log/push_gate.jsonl",
)

def send(chat_id: str, text: str) -> str:
    with gate.reserve((chat_id, text)) as slot:
        if not slot.allowed:
            return f"dropped: {slot.reason}"
        try:
            http_client.post(url, json={"chat": chat_id, "text": text})
            slot.success()
            return "sent"
        except Exception:
            slot.failure()
            raise
```

**Tested on:** Python 3.11. 12 pytest cases, all green. Fake clock, no sleeps.

**Install:** `bash install.sh` drops `push_gate.py` into your project's
`infrastructure/` directory (override with `SP_INSTALL_DIR`).
