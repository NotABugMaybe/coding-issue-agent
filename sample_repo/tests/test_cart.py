from shop.cart import calculate_total


def test_full_price_item():
    assert calculate_total([{"price": 10, "quantity": 2}]) == 20


def test_discounted_item():
    assert calculate_total([{"price": 10, "discount": 0.2, "quantity": 2}]) == 16
