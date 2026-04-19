# unit_conversion_tests

**What:** A pytest regression template for unit assumptions at API
boundaries. You copy `test_template.py` into your project, point it at
your real adapter, and get test coverage over the four things that
silently break when an upstream changes unit: type, unit, scale,
boundary.

**Why:** A financial API returned account balance in integer cents.
The adapter assumed dollars. The displayed value was 100x wrong for
eight days before anyone noticed, because the wrong number was still
plausible — "$5,000 balance" looked fine until I reconciled against
the provider statement. A single regression test that asserted "raw
100 cents → 1.00 dollars" would have caught it on commit. This skill
is the shape of that test, generalized so you can drop it in front of
any numeric API.

**Pattern:** for every API that returns a number, assert all four:

1. **Type.** Is it `int`, `float`, or `Decimal`? If your codebase cares
   about precision (money, time, coordinates), `Decimal` is probably
   what you want. A template test locks the return type in place, so a
   well-meaning refactor to `float` triggers a red test.

2. **Unit.** Cents vs dollars, meters vs feet, milliseconds vs seconds,
   basis points vs percent. Unit metadata is *context* — if the
   response does not include the unit, the adapter must refuse the
   value. "Assume the historical unit" is how 100x bugs get shipped.

3. **Scale.** Multiply by exactly one factor, in exactly one place.
   Put the factor behind a module-level constant (e.g.
   `CENTS_PER_DOLLAR = 100`) so a code reviewer sees it.

4. **Boundary cases.** Zero. Negative. Very large. Very small. The
   template parametrizes a handful; add more that match your domain
   (market closed, account suspended, max-int-like sentinel).

**Usage:**

```bash
# Copy template into your tests, rename the import.
cp test_template.py   my_project/tests/test_balance_adapter.py
cp example_api_wrapper.py my_project/adapters/balance_adapter.py

# Edit test_balance_adapter.py:
#   - change the `parse_balance` import to your adapter
#   - change `simulated_api_response` to match your real JSON shape
#   - adjust EXPECTED_MIN/MAX/PRECISION for your domain
pytest my_project/tests/test_balance_adapter.py
```

**A cheap mental checklist for API reviews:**

Every time you add an adapter that consumes a number from an external
source, answer these five questions out loud to a rubber duck before
merging:

- What Python type is the field?
- What unit is the field?
- What does the field say if the unit is missing or unexpected?
- What is the range I expect? What happens at zero? At negative? At
  the maximum?
- If the upstream changes any of the above, does my test suite go red?

**What this is NOT:**

- Not a property-based testing library. Use Hypothesis if you need
  that. These are targeted examples of the failures I actually saw.
- Not a schema validator. It asserts properties of the parsed
  output, not the wire format.

**Tested on:** pytest 7.x, Python 3.11. The included reference adapter
passes the template tests out of the box.

**Install:** `bash install.sh`.
