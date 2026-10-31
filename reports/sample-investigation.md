# Investigation: Cart total ignores discount

**Repository:** `/Users/lq/Documents/Codex/2026-10-24/2h/coding-issue-agent/sample_repo`

> Read-only investigation. Ranked files are leads; confirm the execution path before treating a cause as established.

## Issue summary

# Cart total ignores discount

When a cart contains a discounted item, `calculate_total` returns the original price instead of the discounted price. The checkout summary shows the wrong total. Items without a discount work correctly.

Expected: total should use the discounted unit price multiplied by quantity.
Actual: total uses the original unit price.

## Ranked files and evidence

### 1. `shop/cart.py` — score 19

Signals: `cart`, `discount`, `item`, `items`, `price`, `quantity`, `the`, `total`

- `shop/cart.py:2` — `"""Return the cart total for a list of item dictionaries."""`
- `shop/cart.py:9` — `total += price * quantity  # BUG: discounted_price is calculated but ignored`
- `shop/cart.py:4` — `for item in items:`
- `shop/cart.py:5` — `price = item["price"]`
- `shop/cart.py:6` — `discount = item.get("discount", 0)`

### 2. `tests/test_cart.py` — score 15

Signals: `cart`, `discount`, `price`, `quantity`

- `tests/test_cart.py:9` — `assert calculate_total([{"price": 10, "discount": 0.2, "quantity": 2}]) == 16`
- `tests/test_cart.py:5` — `assert calculate_total([{"price": 10, "quantity": 2}]) == 20`
- `tests/test_cart.py:1` — `from shop.cart import calculate_total`

## Likely investigation steps

1. Reproduce the reported behavior with the smallest stated input.
2. Trace the relevant code and callers from the cited snippets; verify that the path reaches the reported behavior.
3. Compare current behavior with the expected result and inspect nearby tests.
4. Make the smallest justified change and add a regression test that fails before the fix.
5. Run the focused test and the repository's relevant broader checks.

## Proposed regression test

Create a focused test using the report's stated input and assert the expected result. Include the unaffected control case described by the reporter. The exact test is provisional until the behavior and API are confirmed.

## Uncertainties

- Retrieval is lexical and may omit semantically relevant files.
- No root cause is confirmed by ranking alone; validate each hypothesis against execution and tests.

## Questions for the reporter

- What exact input and environment reproduce the issue?
- What result is expected, and what result currently occurs?
- Are there compatibility constraints or related tests not mentioned?
