def calculate_total(items):
    """Return the cart total for a list of item dictionaries."""
    total = 0
    for item in items:
        price = item["price"]
        discount = item.get("discount", 0)
        quantity = item.get("quantity", 1)
        discounted_price = price * (1 - discount)
        total += price * quantity  # BUG: discounted_price is calculated but ignored
    return total
