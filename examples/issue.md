# Cart total ignores discount

When a cart contains a discounted item, `calculate_total` returns the original price instead of the discounted price. The checkout summary shows the wrong total. Items without a discount work correctly.

Expected: total should use the discounted unit price multiplied by quantity.
Actual: total uses the original unit price.
