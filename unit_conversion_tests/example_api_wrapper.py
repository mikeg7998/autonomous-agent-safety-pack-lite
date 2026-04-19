"""
example_api_wrapper — reference adapter the template tests target.

Shows the *correct* shape for a unit-aware balance parser. Copy this
pattern into your own adapter:

  - assert the type of every field you consume
  - assert the unit metadata matches what you expect
  - perform the scale conversion in exactly one place
  - refuse unknown units rather than guess
"""

from __future__ import annotations

from typing import Any


EXPECTED_CURRENCY = "USD"
CENTS_PER_DOLLAR = 100


class MissingFieldError(KeyError):
    pass


def fetch_balance_cents_as_dollars(response: dict[str, Any]) -> float:
    """
    Parse a response of shape:
        {"account": {"balance": <int cents>, "currency": "USD"}}
    and return dollars as float.

    Raises:
        TypeError    - balance is not an int
        MissingFieldError - required key is absent
        ValueError   - currency is not the expected unit
    """
    try:
        account = response["account"]
    except (KeyError, TypeError) as exc:
        raise MissingFieldError("response missing 'account'") from exc

    if "balance" not in account:
        raise MissingFieldError("account missing 'balance'")
    if "currency" not in account:
        raise MissingFieldError("account missing 'currency'")

    balance = account["balance"]
    currency = account["currency"]

    if not isinstance(balance, int) or isinstance(balance, bool):
        raise TypeError(f"balance must be int cents, got {type(balance).__name__}")

    if currency != EXPECTED_CURRENCY:
        raise ValueError(f"expected currency {EXPECTED_CURRENCY}, got {currency!r}")

    return balance / CENTS_PER_DOLLAR
