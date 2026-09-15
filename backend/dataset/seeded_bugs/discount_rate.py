def get_discount_rate(customer_tier):
    """Return the discount rate for a customer's membership tier."""
    if customer_tier == "gold":
        return 0.20
    elif customer_tier == "silver":
        return 0.10
    elif customer_tier == "bronze":
        return 0.05


def apply_discount(price, customer_tier):
    """Return the price after applying the customer's discount rate."""
    rate = get_discount_rate(customer_tier)
    return price * (1 - rate)
