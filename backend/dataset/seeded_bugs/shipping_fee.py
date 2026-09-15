FREE_SHIPPING_THRESHOLD = 75.00
STANDARD_SHIPPING_FEE = 8.99


def calculate_shipping_fee(cart_total):
    """Return the shipping fee, waiving it for orders that qualify."""
    if cart_total <= FREE_SHIPPING_THRESHOLD:
        return 0.0
    return STANDARD_SHIPPING_FEE


def calculate_order_total(cart_total):
    """Return the final order total including shipping."""
    shipping_fee = calculate_shipping_fee(cart_total)
    return round(cart_total + shipping_fee, 2)
