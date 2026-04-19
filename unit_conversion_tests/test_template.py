"""
Unit-conversion regression template for any API that returns numbers.

Copy this file into your test suite, rename the symbols, and wire it
up against YOUR parser. The four test cases are the four assumptions
you must lock down at the API boundary: type, unit, scale, boundary.

If your adapter returns a `Money` or `Decimal` wrapper, the tests still
apply — change `expected_type` to the wrapper class.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

# ---- REPLACE THIS IMPORT WITH YOUR ADAPTER ---------------------------------
from example_api_wrapper import fetch_balance_cents_as_dollars as parse_balance
# ---------------------------------------------------------------------------


# ---- REPLACE THIS FIXTURE WITH YOUR ADAPTER'S INPUT FORMAT ----------------
def simulated_api_response(balance_cents: int) -> dict:
    """Mimic the raw JSON your real adapter consumes."""
    return {"account": {"balance": balance_cents, "currency": "USD"}}
# ---------------------------------------------------------------------------


# These four class-scoped constants are the contract you are asserting.
EXPECTED_TYPE = float
EXPECTED_MIN = -1_000_000.0     # USD dollars the adapter should permit
EXPECTED_MAX = 1_000_000.0
EXPECTED_PRECISION = 0.01       # one cent — tightest reasonable tolerance


class TestUnitContract:
    """Tests for the *output* of your adapter, not its internals."""

    @pytest.mark.parametrize("raw_cents,expected_dollars", [
        (0, 0.00),
        (1, 0.01),
        (100, 1.00),
        (12345, 123.45),
        (99_999, 999.99),
    ])
    def test_scale_is_dollars_not_cents(self, raw_cents: int, expected_dollars: float):
        """The adapter must divide by 100 exactly once. No 100x or 0.01x bugs."""
        out = parse_balance(simulated_api_response(raw_cents))
        assert out == pytest.approx(expected_dollars, abs=EXPECTED_PRECISION)

    def test_type_is_dollars_not_cents(self):
        out = parse_balance(simulated_api_response(100))
        assert isinstance(out, EXPECTED_TYPE), (
            f"Expected {EXPECTED_TYPE.__name__}, got {type(out).__name__}. "
            "Did the adapter return raw cents?"
        )

    def test_boundary_zero(self):
        assert parse_balance(simulated_api_response(0)) == pytest.approx(0.0)

    def test_boundary_negative(self):
        """Real accounts can go negative. Parser must not clamp to zero."""
        out = parse_balance(simulated_api_response(-5000))
        assert out == pytest.approx(-50.00, abs=EXPECTED_PRECISION)

    def test_boundary_large(self):
        """Large-but-plausible balance should round-trip without overflow or loss."""
        out = parse_balance(simulated_api_response(99_999_99))  # $99,999.99
        assert out == pytest.approx(99_999.99, abs=EXPECTED_PRECISION)
        assert EXPECTED_MIN <= out <= EXPECTED_MAX


class TestDefensiveAssertions:
    """Additional assumptions the adapter should enforce at the boundary."""

    def test_rejects_string_where_int_expected(self):
        """If the upstream accidentally returns '100' for balance, don't silently coerce."""
        with pytest.raises((TypeError, ValueError)):
            parse_balance({"account": {"balance": "100", "currency": "USD"}})

    def test_rejects_missing_currency(self):
        """Unit metadata missing means unit is unknown. Refuse."""
        with pytest.raises((KeyError, ValueError)):
            parse_balance({"account": {"balance": 100}})

    def test_rejects_wrong_currency(self):
        """If the unit changes, the adapter must refuse, not silently convert."""
        with pytest.raises(ValueError):
            parse_balance({"account": {"balance": 100, "currency": "EUR"}})


class TestDecimalVariant:
    """If precision matters for billing, Decimal is the right return type.

    Enable by swapping EXPECTED_TYPE above to `Decimal` and switching
    your adapter to return `Decimal`.
    """

    @pytest.mark.skip(reason="enable only if adapter returns Decimal")
    def test_no_binary_float_drift(self):
        out: Any = parse_balance(simulated_api_response(10))
        assert isinstance(out, Decimal)
        assert out == Decimal("0.10")
